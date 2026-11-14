#!/usr/bin/env python3
"""HZ01-HZ116: Herdr, la finestra di Arturo (8/11/2026, ramo di prova `herdr`).

La fonte del banco sta nel repository di Volta (volta/test_herdr.py, dal 14/11/2026): volta/pubblica-mod.py
lo copia nel repository di Arturo come tests/test_herdr_2026_11_08.py, insieme al mod. La copia non si
modifica a mano. Lanciato dal repository di Volta, il banco copia arturo/ in una cartella temporanea come
shared/volta/ e salta, dichiarandoli, i casi che chiedono file di Arturo (bin/arturo, hooks/, commands/...).

/setup installa Herdr (herdr.dev) con `shared/volta/installa-herdr.sh`, e l'hook `hooks/herdr-stato.sh`
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
HZ17 Volta, i gruppi (sessioni.js con node, #5068): per macchina nell'ordine del file con la nota
     della macchina giù; per progetto con la nota sull'ultimo gruppo; dentro il gruppo la più recente,
     poi l'alfabeto (HZ51); i nomi automatici ("claudecode-ca") lasciano il posto alla risposta.
HZ18 Volta, il clic (sessioni.js con node): una sessione in background si aggancia con l'argv
     del file (locale o ssh), un'interattiva ferma passa da porta-volta, una al lavoro, che aspetta o di
     una macchina giù no, col motivo; la scheda già aperta si riconosce anche dall'argv avvolto da zsh
     da un ciclo ssh dentro sh -c e da pwsh -Command su Windows, senza prendere un id che ne contiene un altro.
HZ19 Volta nella barra: barra.js monta volta.js e accetta il comando volta-<id>, volta.js
     lancia teletrasporto.py volta --scrivi e porta-volta, e senza teletrasporto.py non mostra niente.
HZ20 Volta su Windows (9/11/2026): volta.js lancia volta_sonda.py e teletrasporto.py col Python di arturo.json
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
     (node) e di bin/note_finestra.py dicono lo stesso; l'aiuto di arturo note e docs/volta.md
     spiegano --chi e --json, e la guida parla a chi usa Arturo. Fra due note aperte con lo stesso numero
     (nate su due macchine) lo tiene la più vecchia, uguale in noteAperte e in numerate.
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
     rilanciato, togli lascia il file com'era, un blocco senza la riga di fine resta com'è con NASCITA
     SENZA FINE (prima togli cancellava il resto del .zshrc, #5265), stato vede la funzione claude della persona fuori dal
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
     respawn e rm qui o con hc exec --on, rifiuta un verbo o un id strani senza lanciare niente, trova
     claude anche fuori dal PATH di hc exec (~/.local/bin dei Mac, #5555, con python3), e
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
     Sul Mac, dove hc exec non trova claude, Riavvia riprova con python3 (#5555). Un Mac senza
     LaunchAgent risponde "hc-run" col percorso intero di claude, e hc run lancia quello (#5560);
     un percorso strano dà claude nudo. SERVIZIO vero su un Mac, chiesto da remoto, dà il percorso.
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
HZ50 le note si trovano a vista (11/11/2026): il piede della barra ha l'icona "Note", che apre l'elenco
     e porta nel suggerimento i tasti della nota nuova e dell'elenco; dal 13/11 (#5371) il piede è una fila
     di icone e il layout arturo gli dà l'altezza PIEDE di misure.js (44 px).
HZ51 Volta, l'ordine è l'ultima interazione (11/11/2026): dentro un gruppo la sessione toccata per
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
     che si sta ancora avviando non è nuda. Una sessione appena nata non ripassa dal servizio. Su Windows
     nuda la decide lo schermo (prompt PS), e comando() scrive per PowerShell (& e apici raddoppiati).
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
HZ56 shared/volta/ è una copia (11/11/2026): la scrive volta/pubblica-mod.py del repository di
     Volta, e ogni file ha l'impronta di ORIGINE. Un file toccato a mano, uno in più o uno in
     meno fanno rosso: la fonte si cambia là.
HZ57 il mod si aggiorna da solo (11/11/2026): volta.js chiede a volta_mod.py un controllo all'apertura e
     ogni ora, mai due insieme, e pubblica la versione in shared arturo.mod; dal 13/11 il menu di Impostazioni
     (comuni.js) la scrive, e il piede la porta nel suggerimento; prima la scriveva accanto
     a Impostazioni con rigaMod() di sessioni.js (node): ora dell'installazione, giorno se non è oggi,
     avviso dopo un giorno senza controllo, avviso quando il plugin di Arturo è fermo per una possibile
     compromissione (volta_mod.py programmi, 12/11/2026).
HZ58 il nome e il progetto scritti dalla persona (#5292): i verbi rinomina e progetto di volta_sonda.py
     scrivono cache/titolo e cache/scheda della sessione con fonte "persona", qui e su un'altra macchina
     (hc finto); un progetto che non è uno slug e un id strano non partono. hooks/titolo-sessione.py non
     riscrive un nome della persona e non lo spazza finché la sessione ha una trascrizione; senza nome
     il file sparisce e il titolo torna al modello. hooks/scheda-terminale.py tiene il progetto della
     persona davanti a un altro /inizio e a un file scritto altrove, e a SessionEnd lascia il file. La
     sonda porta nell'elenco daPortare finché Claude Code non ha il nome (--portato).
HZ59 nome e progetto si cambiano dalla finestra (#5292): il menu ha Rinomina e "Sposta in un progetto…",
     che aprono il dialogo di cambio.js, come il doppio clic sul titolo, e il titolo del dialogo del
     progetto ripete la voce del menu senza i puntini (#5504); il dialogo manda il comando
     arturo.volta-cambia-<cosa>-<esadecimale>-<id>, che barra.js legge prima del clic su una sessione
     (sessioni.js con node: codifica, leggiCambio, nomeNuovo, progettoNuovo, progettiNoti, casellaVuota).
     dati.js (herdr finto): cambiaSessione chiama la sonda sulla macchina della sessione col sessionId;
     rinominaSchede rinomina la scheda sola; portaNome scrive /rename solo a sessione ferma, con Claude
     nella scheda e la casella vuota, e poi segna --portato; spostaScheda chiude l'aggancio e lo riapre
     nello spazio del progetto nuovo, e lascia dov'è un'interattiva che gira in una scheda.
HZ60 il clic trova la scheda di Herdr anche su Windows (#5289): terminale_di() di volta_sonda.py legge
     HC_TERMINAL_ID dall'ambiente di un processo vero, con ps sul Mac e dalla memoria del processo su
     Windows; un processo fuori da Herdr e uno che non esiste danno None. La SONDA porta dentro la
     funzione e la chiama solo per le interattive. La sonda verso un'altra macchina viaggia compressa:
     la riga torna identica alla SONDA e resta sotto gli 8000 caratteri di una riga di cmd.exe.
HZ63 il microfono di questa macchina arriva alle sessioni di un'altra (11/11/2026): microfono.js (con node)
     dà il bersaglio solo per una scheda che aggancia con ssh una sessione di un'altra macchina, accende,
     rinnova e spegne un minuto dopo che il fuoco è passato altrove. volta_microfono.py con un audio
     finto: ricevi mette il microfono virtuale e rimette l'ingresso di prima a fine flusso, su SIGTERM e
     dopo il silenzio di una rete caduta; rifiuta un secondo ponte; senza BlackHole non tocca niente;
     non rimette un ingresso scelto a mano nel frattempo; ripara agisce solo se il ponte è morto;
     accendi e spegni tengono il ponte locale, che scade da solo senza rinnovo.

Con --avvelena le copie rotte del repository devono far rosso il caso che le sorveglia.
HZ61 i progetti vengono dalla memoria di Arturo (11/11/2026): barra.js chiede `arturo progetti --json`
     (dati.js progettiMemoria) e solo se manca ricade su cartelle e `todo progetti`. dati.js con node:
     un nome alternativo della fonte e lo slug degli handoff sono una riga sola, coi conti dei todo; un
     progetto che vive solo negli handoff ha la sua riga; una cartella che Arturo non conosce resta fra
     le "Altre cartelle"; l'ultimo handoff più vecchio di un mese manda il progetto nella sezione chiusa
     in fondo; con la memoria le cartelle non si aggiungono due volte; 150 voci stanno sotto i 50 ms;
     senza memoria l'elenco è quello di prima. Apri un progetto e Cambia progetto leggono nomiProgetti.
HZ62 il velo delle note sceglie il singolo elemento (nota.js con node): nomeElemento() dà il nome da id
     fissi e prefissi; elementoSotto() prende il più piccolo sotto il punto fra quelli di window.elements(),
     lascia fuori il velo stesso e distingue due parti con lo stesso id; evidenza() mette l'elemento prima
     della parte e senza elementi resta com'era; il todo della nota nomina l'elemento.
HZ64 notaui.js usa gli elementi solo se la finestra li dà (Volta), accende e spegne il registro,
     salva l'elemento nel dove; le parti danno un id agli elementi che non l'avevano.
HZ65 il testo di un todo non finisce in una shell (revisione dell'11/11/2026, dati.js con node): se nella
     scheda agganciata claude attach è uscito, Lavoraci e i suggerimenti non scrivono il testo; la
     sessione giusta, presa da sessioni.json per id, riparte nella sua scheda e un avviso dice di
     riprovare; se Volta non la elenca più o il servizio non parte lo dice, e non scrive niente. Con
     Claude nella scheda, e con un agente di Herdr, il testo parte come prima.
HZ66 una nascita rimasta a metà non blocca le altre (revisione dell'11/11/2026, dati.js con node): shared
     arturo.nascita è { macchina, da } e scade dopo 7 minuti; la stringa della versione di prima è
     scaduta; una nascita fresca rifiuta la seconda e lo dice con un avviso; a nascita finita il segno
     sparisce; una sessione nata che non si apre lo dice con un avviso.
HZ67 la nascita passa dalla barra (comandi.js con node): instrada() dice verbo, argomento e se il comando
     è lungo, e legge volta-nuova, volta-menu-, volta-altro-, volta-cambia- e volta-gesto- prima di
     volta-<id>; le finestre Apri un progetto, La settimana e Cosa posso chiedere mandano il comando e si
     chiudono, senza await; il benvenuto manda arturo.nuova; il ciclo di barra.js ha il try per comando
     e non aspetta i comandi lunghi.
HZ68 con la barra nascosta i comandi li rimanda la barra di stato (comandi.js con node, testata.js): solo
     a barra nascosta, mai il comando di controllo né un comando sconosciuto; mostra la barra, aspetta
     che risponda e rimanda.
HZ69 una lettura dell'elenco ha un tetto solo (revisione dell'11/11/2026, volta_sonda.py): ATTESA_LETTURA
     sta sotto l'attesa di volta.js; con una macchina che non risponde il documento esce lo stesso entro
     il tetto, con le altre macchine lette e quella segnata irraggiungibile con le righe di prima; hc exec
     e la sonda sulla macchina ricevono i secondi che restano; claude agents dentro la sonda non aspetta
     oltre.
HZ70 se Herdr non dice le macchine restano quelle di prima (volta_sonda.py): hc machine ls che esce male,
     che risponde altro o che non fa in tempo lascia le macchine dell'ultima lettura, irraggiungibili,
     con le loro righe; un elenco vuoto vero le toglie; nasci dice che Herdr non risponde; su Windows hc
     si cerca con .exe.
HZ71 un avviso prima del JSON di claude agents non svuota la macchina (volta_sonda.py): l'elenco si legge
     dal primo "[" che apre un elenco, qui e su una macchina senza Python; se claude agents esce male o
     non dà un elenco la macchina è irraggiungibile col motivo e tiene le righe di prima; la nascita
     legge il sessionId intero anche con l'avviso e riprova se la sessione non è ancora in elenco.
HZ72 una riga della trascrizione che non è un oggetto non ferma la sonda (volta_sonda.py): un numero, una
     stringa, un elenco o un messaggio che non è un oggetto si saltano, e le ultime parole si leggono.
HZ73 l'esito di uno script si legge col codice d'uscita (dati.js con node): esito() prende l'ultima riga
     che inizia con "{"; uscita vuota, riga rotta o codice diverso da 0 senza errore sono un errore col
     motivo scritto dallo script; lo usano prepara, la nascita, Rinomina, i gesti e porta-volta.
HZ74 il progetto resta col lavoro (revisione dell'11/11/2026, volta_sonda.py): una fonte forte scrive il
     registro cache/volta-lavori/<lavoro>.json; dopo /clear (sessionId nuovo, scheda dalla cartella o
     nessuna scheda) la riga tiene il progetto del registro; il testo dopo /inizio non ancora risolto
     si vede ma non entra nel registro; una fonte forte nuova lo aggiorna; un altro lavoro non eredita.
HZ75 la cartella base non è un progetto (volta_sonda.py): con fonte "cartella" e senza registro il nome
     della base dei progetti di Volta (arturo.json) o della casa dà progetto vuoto, un repo vero resta;
     un'interattiva ha il registro sul suo pid; la pulizia toglie il pid sparito e il lavoro non più
     elencato da 14 giorni, e lascia quelli elencati, anche chiusi da più di tre giorni.
HZ76 la nascita scrive subito il registro e il nome resta col lavoro (volta_sonda.py): nasci scrive il
     registro anche se non legge il sessionId; il nome dato dalla persona passa al sessionId nuovo, già
     portato, e resta alla lettura dopo; un titolo automatico non si eredita; Rinomina vuoto lo toglie
     e non torna al /clear seguente.
HZ77 una sessione già agganciata in un Terminale non si apre due volte (revisione dell'11/11/2026, dati.js
     con node e volta.js): altrove(s) trova i terminali di questa macchina che la agganciano fuori dai
     pannelli, per argv e per etichetta, e non quelli chiusi, di un'altra macchina o di un'altra
     sessione; con una scheda nella finestra è vuoto; stacca(s) li chiude e la scheda nuova nasce dopo;
     il primo clic avvisa e si ferma, il secondo stacca e apre.
HZ78 il microfono torna su un ingresso vero (revisione dell'11/11/2026, volta_microfono.py con l'audio
     finto): se l'ingresso di prima è sparito torna il primo che non è il virtuale, a fine flusso e con
     ripara; il virtuale non si salva mai come "prima"; un pid salvato che oggi è un altro programma, o
     questo script in un altro ruolo, non passa per un ponte vivo; la sonda delle sessioni lancia ripara
     quando trova microfono.json, e non tocca un ponte vivo.
HZ79 il ponte non resta appeso: un'uscita audio che non legge più chiude il ricevitore entro il tetto e
     l'ingresso torna; spegni chiude cattura e ssh anche quando il ponte è stato ucciso, e non tocca un
     pid che oggi è di un altro programma.
HZ80 l'errore di chiave ssh ha la sua frase, diversa dal permesso del microfono e dalla macchina che non
     risponde; bersaglio salta una macchina Windows, riconosciuta dal percorso di claude nell'argv.
HZ81 la colonna di sinistra tiene a vista il piede (revisione dell'11/11/2026; dal 12/11 l'elenco di Volta
     prende tutta l'altezza, HZ90): il riquadro dei gesti ha al più 160 px e scorre, la radice della barra
     taglia quello che non entra e misura la sua cima; nel layout il divisore sopra il piede non si trascina
     (un trascinamento salvato in layouts/.state aveva portato il piede a 101 px) e il piede è alto PIEDE px:
     la misura cambiata fa cadere quel trascinamento al primo caricamento.
HZ82 un tasto di Arturo rimasto su un mod tolto si riallinea (revisione dell'11/11/2026): sul MacBook ⌘O
     puntava a mod.open:arturo-progetti e non apriva niente. installa-herdr.sh tratta i tre valori esatti
     (mod.open:arturo-progetti, -chrome, -stato) come un tasto libero; tasti() di volta_mod.py fa lo stesso
     a ogni aggiornamento del mod. Un tasto che la persona usa per altro, un valore solo simile e un tasto
     che non è di Arturo restano; i due elenchi sono uguali.
HZ83 nomi di sessioni e progetti (revisione dell'11/11/2026, sessioni.js con node): un progetto fatto di soli
     separatori ("-") vale "Senza progetto" e non fa cadere la barra; un nome è automatico solo se manca, è
     l'id, oppure è "<ultimo pezzo della cartella>-xx" con due cifre esadecimali (anche con un percorso di
     Windows e con maiuscole e spazi nella cartella). "bando-57" in un'altra cartella resta il titolo.
HZ84 lo spazio "Volta" non è un progetto e "Altra conversazione" fa nascere una sessione vera: eProgetto di
     dati.js (con node) scarta lo spazio "volta", quelli senza nome e quelli di un'altra macchina, e
     progetti() non lo mette nella barra; il pannello Da fare lo usa per il progetto attivo; il pulsante
     della testata lancia arturo.volta-nuova, che la barra porta a nuovaScheda(), e non più tab.new con claude.
HZ85 la spunta di un todo e /rename (revisione dell'11/11/2026): ancoraFatti di azioni.js (con node) tiene le
     spunte dei todo ancora in elenco, in ogni gruppo, e il pannello la usa al posto di fatti.clear(); "fatto"
     scrive arturo.scritto, così la barra rilegge i conti. portaNome di dati.js (con node, orologio finto)
     non riscrive lo stesso nome per 5 minuti e intanto riprova solo a segnarlo alla sonda; un nome nuovo,
     un'altra sessione e i 5 minuti passati lo riscrivono; un /rename non riuscito non conta come scritto.
HZ86 ⌘↓ e ⌘↑ girano fra tutte le sessioni dell'elenco (12/11/2026): keys.json li lega ad
     arturo.volta-giro-avanti e -indietro, instrada() li legge prima di volta-<id>, la barra li porta a
     Volta.giro(). sessioni.js con node: ordineGiro() prende le sessioni che lavorano o aspettano e le ferme
     con una scheda aperta, anche nascoste, e lascia fuori quelle che stanno in un Terminale; statoGiro() tiene l'ordine dentro una raffica di tasti; passoGiro() gira
     in tondo; sessioneDi() riconosce la scheda in primo piano per etichetta, argv o terminale.
HZ87 il motivo di una sessione che non si apre (11/11/2026, #5358): motivoUscita di sessioni.js (con node)
     legge dallo schermo della scheda perché Claude è uscito, guarda solo l'ultimo aggancio scritto nella
     shell, e dice `fermo` quando riprovare non serve (macchina che non si raggiunge, cartella illeggibile,
     sessione che non c'è più). La veglia di dati.js (con node) mette quella frase sulla riga, non riavvia
     per una causa ferma e riavvia una volta sola per le altre. Una scheda che vive su un'altra macchina
     (indirizzo "macchina/t7") non conta come scheda di questa finestra: il clic ne apre una qui.
HZ88 il terminale si legge (12/11/2026, #5365): nei due temi (notte e carta) il testo e ogni colore della
     shell che porta testo (ansi 1-15) reggono 4,5:1 sul fondo, il testo regge 4,5:1 sulla selezione, e la
     cornice del terminale nel layout usa i nomi del tema (niente esadecimali fissi, che col tema chiaro
     restano scuri).
HZ89 chiudere una sessione la chiude davvero (12/11/2026, decisione di Federico): ⌘W, la X o Chiudi del
     menu fanno il congedo, /fine e poi claude stop. sessioni.js con node: visibili() toglie dall'elenco
     le chiuse e quelle in congedo, sparite() trova le schede chiuse da chi usa la finestra (non quelle
     tolte da Volta, non una sessione che ha ancora un'altra scheda), passoCongedo() aspetta il turno,
     riprende con /fine, ferma a /fine finito e ferma lo stesso dopo una domanda o un tetto; segna
     salvata solo a /fine finito, e solo una salvata e chiusa va eliminata con claude rm (#5401). La sonda:
     congeda fa claude stop e poi --resume della stessa conversazione col solo /fine, senza
     --fork-session e mai rm; righe() segna chiusa una sessione in background senza processo né status.
     volta.js guarda le schede, Chiudi passa dal congedo e l'elenco usa vis(); dati.js segna le schede
     che chiude Volta stessa.
HZ90 la colonna di sinistra e la testata più leggere (12/11/2026): la barra non ha più la sezione dei
     progetti aperti e l'elenco di Volta prende tutta l'altezza, senza tetto; l'intestazione di un gruppo
     per progetto apre il progetto. La testata non ha più Cosa posso chiedere né Altra conversazione, e
     sotto il titolo dice la macchina della sessione (arturo.volta.dove), col nome breve: macchinaBreve()
     di sessioni.js (con node). Lo stato idle non si legge più "Conversazione aperta".
HZ91 i titoli veri dei progetti (12/11/2026, #5367): sessioni.js con node, dopo impostaProgetti(),
     nomeProgetto() dà il titolo noto, gruppi() mette un nome alternativo nel gruppo del suo progetto e
     filtraProgetti() trova un progetto anche dal titolo; volta.js e cambio.js impostano la mappa prima
     del disegno, la barra porta la chiave nella mappa, e progetti() di dati.js tiene il titolo della
     memoria anche per un progetto coi todo.
HZ92 le fasi delle sessioni (#5366, nota di Federico dell'11/11: "le ferme devono essere diverse"):
     sessioni.js con node. fase() divide la "ferma" della sonda in stasi (Claude ha chiuso il turno
     chiedendo qualcosa: "Scrivimi **1**", una domanda, "Prossimo passo" della persona, nessun testo di
     Claude) e attesa (ha finito: "Niente da fare per te", un passo di altri); fraseStato() dice "Ti
     aspetta da" e "Aspetta un comando da"; mostrate() tiene a vista chi ti aspetta e nasconde dietro "N
     in attesa di comando" solo chi aspetta un comando. La sonda passa interazione, coda, chi e
     fineFatta dalla trascrizione (provata su una trascrizione finta).
HZ93 la chiusura automatica (#5366): sessioni.js con node. daCongedare() prende solo le sessioni di
     questa macchina, in background, in attesa di comando da più dell'ora, senza scheda aperta, senza
     lavoro lasciato in corso e non già in congedo, la più vecchia per prima; restanti() tiene i tetti
     di 3 all'ora e 12 al giorno; registroProva() tiene la prima volta che ha visto una sessione;
     passoCongedo() ferma senza un secondo /fine chi l'ha già fatto. volta.js: in modo "prova" scrive
     solo il registro, una chiusura alla volta, registro scritto col testo di prima; dati.js: modo di
     serie "prova"; la sonda: congeda --auto col suo testo di /fine.
HZ94 le animazioni di Volta (12/11/2026, #5410): sessioni.js e comandi.js con node. entrate() dà solo
     le sessioni nuove fra due letture, niente alla prima; motoRiga() parte da 0 senza transizione, poi
     va a 1 col ritardo della scala (al più 120 ms), ed esce verso 0 più in fretta di come entra, tutto
     entro 300 ms; i comandi arturo.movimento e arturo.impostazioni. comuni.js: senza movimento il segno
     torna il pallino fermo, la stella gira e il pallino pulsa solo col movimento acceso, anche "Riduci
     movimento" del Mac lo spegne. volta.js: la riga in congedo si dissolve prima del congedo, che parte
     una volta sola; col movimento spento niente ritardo.
HZ95 la scheda mostra chi ci gira (12/11/2026, volta a12c0dd): una scheda nata per agganciare una sessione
     di un'altra macchina (argv ed etichetta) che ora ospita un'interattiva di questa macchina (campo
     terminale della sonda) è dell'interattiva: sessioneDi dà l'interattiva, schedeAgganciate non la conta,
     e con arturo.volta.dove.occupate in shared schedeDi della sessione di nascita è vuoto. La testata
     (schedaAgganciata, statoSpazio; volta 4e4eada ed ea206f8) legge l'id anche da pwsh -Command e da
     sh -c, e una scheda occupata è dell'interattiva che ci gira.
HZ96 le tessere dei progetti su ⌘T (12/11/2026, #5371): nel layout lo stack "lavoro" tiene il terminale
     (main, mostrato all'avvio) e la parte casa; arturo.casa mostra le tessere col campo vuoto,
     arturo.casa-chiudi ed Esc tornano al terminale, la barra all'avvio rimette il terminale e scrive i
     progetti delle tessere; casa.js non torna al terminale quando nasce. tessere.js con node: prima
     "Nuova richiesta", poi i progetti in ordine; il filtro mette prima chi comincia così; colonne, frecce
     che si fermano ai bordi, iniziali, tinta stabile, immagine solo se è nell'elenco arrivato. Dal
     13/11 (#5456): la tessera Nuova richiesta e la guida scrivono il tasto della macchina (Ctrl+Shift+T su
     Windows) e la guida nomina le tessere; con un layout senza lo stack ⌘T apre la sessione nuova e il
     ritorno al terminale non manda layout.select; una nota sulle tessere mostrate va alla parte "Tessere
     dei progetti", non alla sessione.
HZ97 le note fra le macchine partono (12/11/2026, #5447): volta_note.py si importa accanto a volta_sonda.py
     e trova le sei funzioni che ne prende; volta.js lo cerca nella cartella del mod e lo lancia dopo
     ogni giro dell'elenco, con lo stato in ~/.cache/volta-note/stato.json (cacheVolta("volta-note"), #5449).
HZ98 la ricerca di ⌘K (#5369, nota di Federico dell'11/11: "accedere a chat e progetti"): sessioni.js con node.
     cerca() mette in un elenco solo sessioni e progetti, prima chi comincia col testo e poi chi lo contiene,
     senza maiuscole né accenti, cerca anche nel titolo e nei nomi alternativi del progetto, tiene in fondo
     le chiuse e chiude con Nuova richiesta; senza testo dà le sessioni vive più recenti, poi i progetti.
     comandoNuova() torna intero con decodifica(); apri.js legge le sessioni di Volta e usa cerca().
HZ99 i tasti della ricerca (#5369): ⌘K e ⌘O aprono Cerca, su Windows Ctrl+Shift+A; la barra decodifica il
     testo di arturo.nuova-<esadecimale>; tasti() dice ⌘K e il giro.
HZ100 installa-herdr.sh senza keys.json parte dai tasti di serie di Herdr (shared/volta/keys-herdr*.json):
     Volta ha ⌘W, ⌘C e gli altri, la sezione terminal, e i tasti di Arturo sopra, ⌘T sulle tessere (#5369).
HZ101 la riga accesa, il comando di Sposta su e la tessera che fa nascere una conversazione nel progetto
     (conversazione-<slug>, casa.js e barra.js; 12/11/2026, Federico): sessioni.js con node: corrente() è
     l'ultima sessione del giro dentro la raffica di ⌘↓ e ⌘↑, poi quella della scheda in primo piano;
     sessioneDavanti() riconosce chi gira nel terminale di una scheda in uno spazio di un'altra macchina
     (torre/t13) prima dell'etichetta; unaPerConversazione() toglie la copia ferma di una sessione
     spostata. comandi.js legge volta-sposta-<macchina>-<id>; testata e main.js hanno pulsante e popup.
HZ102 Sposta su porta la conversazione (12/11/2026): gli script di volta_sposta.py su due macchine finte
     nella stessa casa. LEGGI rifiuta file non salvati e commit non spinti e una cartella fuori dalla base;
     PREPARA clona il repository allo stesso commit sull'altra base e trova la cartella di Claude codificata;
     PACCO e SCARICA portano trascrizione e cartella, tengono da parte la copia di prima e rifiutano un
     pacco con un nome fuori dalla cartella; SEGNA scrive il progetto con fonte teletrasporto, senza /inizio.
HZ103 trascinare una sessione su un altro progetto (12/11/2026, Federico: "voglio poter fare drag & drop"):
     sessioni.js con node: mosso() passa da clic a trascinamento a MOSSA_PX; arrivoTrascino() dà lo slug
     del progetto d'arrivo e null sullo stesso progetto, nella vista per macchina, su "Senza progetto",
     senza movimento e con la macchina giù. volta.js: la pressione sulla riga solo per progetto, il
     movimento sull'elenco, il rilascio sul gruppo che chiama cambia() come Cambia progetto, il clic
     che non apre dopo un trascinamento.
HZ104 Sposta su dal menu e Sposta tutto su (12/11/2026, Federico: "senza interromperlo"): sessioni.js con
     node: spostabili() prende le sessioni in background vive delle altre macchine, anche chi lavora, e
     lascia fuori interattive, chiuse, in errore e di macchine giù; contoTutto() dice quante e quante a
     turno finito; menu() ha Sposta su… solo in background; comandi.js legge volta-spostatutto-<macchina>.
     volta_sposta.py rifiuta con lavora: true se la sessione fa un turno, prima di leggere e prima di
     fermarla, e si ferma se claude stop fallisce e la sessione ha ancora un processo (#5574); volta.js fa girare la coda a ogni giro e non parte su chi lavora; barra, menu e main.js
     hanno la pastiglia, la voce e il popup.
HZ105 la colonna di sinistra sulla scala comune (13/11/2026, #5371, fase 4 del piano di design): misure.js
     dà spazi, margine, raggi, testo, pulsanti e l'altezza del piede; la cima ha il campo "Cerca o chiedi"
     che apre la ricerca (⌘K) e Nuova richiesta a icona, senza più "Apri un progetto"; il piede è una fila
     di pulsanteIcona col nome nel suggerimento e per la lettura a voce; gruppi e righe di volta.js partono
     dallo stesso MARGINE; lo schermo di claude logs prende il font dalle impostazioni.
HZ106 le nascite che cadono (13/11/2026): la SONDA legge i lavori di <config>/jobs e segna la macchina
     rotta con tre crash "before init" su più lavori negli ultimi 30 minuti, senza una nascita riuscita
     dopo; il documento porta `nascita` nella voce della macchina; l'intento del congedo segna la riga.
HZ107 il clic non fa ripartire una sessione in errore su una macchina rotta, né la veglia; l'avviso arriva
     una volta per episodio; i gruppi dicono "non fa partire sessioni"; arturo() ha un tempo massimo.
HZ108 i congedi rimasti a metà di questa macchina: stop se vivi con /fine in fondo, rm se fermi o in
     errore, niente su una riaperta, una recente, una nel registro o una viva con la scheda aperta; una
     ferma si elimina anche con la scheda aperta, dove resta solo la shell; una ritirata senza /fine in fondo
     (riaperta dopo il congedo) resta.
HZ110 Volta rilegge l'elenco solo quando cambia sessioni.json (tocca), non per il clone del mod o il
     microfono; arturo() tiene un solo comando in volo e dopo uno appeso non ne lancia altri per 5 minuti
     (voloArturo); cartelle() ha un tempo massimo; nessuno scrive più arturo.volta.errore.
HZ111 lo spostamento parte staccato (13/11/2026): sposta --esito risponde subito {"avviato"}, il figlio
     scrive l'esito finito nel file anche quando cade, Volta lo legge a giri con cx.sleep fino a 25 minuti
     (esitoSposta) invece di chiedere a exec 20 minuti oltre il tetto di 10.
HZ113 una fonte sola per il progetto (#5487, 13/11/2026): progettoDi di sessioni.js porta un nome
     alternativo ("volta", "Volta Celeste") alla chiave della scheda; chiaveProgetto, canonico e spazio di
     dati.js passano da lì (con node). aggancia mette la sessione di "volta" nello spazio herdr-arturo, mai
     in uno spazio "volta" (che libera() rinominerebbe "Senza progetto"), anche quando lo spazio del
     progetto porta un nome alternativo; apri("volta") (Lavoraci) va nello stesso spazio; lo spazio libero
     "Volta" di prima resta libero. Testata e colonna leggono il progetto aperto con progettoDi.
HZ114 i messaggi nominano la macchina vera (#5534, 13/11/2026): chi() di volta_sonda.py dà il nome di
     questa macchina per "qui" e per il vuoto, e lo usano gli errori della sonda e di volta_sposta.py;
     nomeMacchina di sessioni.js e di dati.js (con node) legge il nome dall'elenco delle macchine, e
     "La sessione non nasce su ..." dice quel nome, mai "qui".
HZ115 gli script Python del mod non scrivono .pyc nella sua cartella (#5556, 13/11/2026): Herdr ricarica il
     mod a ogni file nuovo che vi compare, anche in __pycache__, e la ricarica ferma per sempre l'attesa
     di Sposta (cx.sleep). volta_sonda.py sposta e volta_note.py, lanciati da una copia del mod, non
     lasciano __pycache__.
HZ116 uno spostamento lasciato a metà da una ricarica del mod riprende (#5559, 13/11/2026): spostaSessione
     segna lo spostamento staccato in cache/volta/sposta/volo.json; riprendiSposta legge l'esito finito,
     apre la scheda d'arrivo e toglie la voce, o con un errore riapre la scheda chiusa; voloSposta scarta
     le voci rotte o di ore fa e lascia quelle che un'altra copia viva segue; Volta le riprende al caricamento.
HZ117 le correzioni piccole della fase F2 (14/11/2026): la colonna di Volta dice anche l'errore della
     lettura dell'elenco (#5575); i gesti su questa macchina trovano claude in ~/.local/bin con la ricerca
     sola trova_claude, che sta anche negli script per le macchine (#5576); statiCorti tiene la copia viva
     di un id che compare due volte, in tutti e due gli ordini (#5577); volta.js legge le risposte dei
     Python con esito() (#5578); pausa() di dati.js aspetta con l'orologio di main.js (cx.sleep) e torna a
     Python solo senza orologio o se l'orologio getta (#5579).
HZ118 lo stacco delle schede ferme (F3.2 di #5587, 14/11/2026): daStaccare sceglie le schede in un pannello
     che agganciano una sessione ferma da 45 minuti, per macchina e id insieme, prima la più vecchia, mai
     quella in primo piano, una che lavora, aspetta o ha un lavoro in corso; staccaAggancio manda Ctrl+Z solo
     se in primo piano gira l'aggancio di quella sessione (anche via ssh) e dice ok solo se la shell torna;
     volta.js stacca ogni minuto e riaggancia la scheda staccata quando torna in primo piano.
HZ119 la chiave macchina:id delle sessioni (S1 del piano F3·S, #5634, 14/11/2026): dopo Sposta su lo stesso id
     c'è su due macchine. La scheda ssh aggancia la copia della sua macchina e quella locale la copia di qui;
     l'etichetta arturo.sessione vale macchina:id, e una vecchia col solo id decide solo se l'id è unico;
     l'elenco tiene la copia viva anche dopo un /clear; il congedo e trova() vanno per macchina e id;
     statiCorti segna l'id doppio per le parti senza elenco; il microfono segue la macchina dell'etichetta;
     volta.js tiene congedi, coda di Sposta e mappe per chiave.
HZ120 i comandi di Volta portano la chiave macchina:id (#5643, 14/11/2026): il menu del tasto destro, il
     dialogo di cambio, Sposta su e la ricerca ⌘K mandano alla barra macchina:id, e comandi.js legge
     volta-sposta-<chiave>-<macchina> anche con trattini nei nomi delle macchine (e la forma vecchia
     volta-sposta-<macchina>-<id>). trovaId trova la copia per chiave; un id nudo che sta su due macchine
     non sceglie la prima copia, ma avvisa; vistaId e Sposta tutto passano la chiave.
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

CASI = ("HZ01", "HZ02", "HZ03", "HZ04", "HZ05", "HZ06", "HZ07", "HZ08", "HZ09", "HZ10", "HZ11", "HZ12", "HZ13", "HZ14", "HZ15", "HZ16", "HZ17", "HZ18", "HZ19", "HZ20", "HZ21", "HZ22", "HZ23", "HZ24", "HZ25", "HZ26", "HZ27", "HZ28", "HZ29", "HZ30", "HZ31", "HZ32", "HZ33", "HZ34", "HZ35", "HZ36", "HZ37", "HZ38", "HZ39", "HZ40", "HZ41", "HZ42", "HZ43", "HZ44", "HZ45", "HZ46", "HZ47", "HZ48", "HZ49", "HZ50", "HZ51", "HZ52", "HZ53", "HZ54", "HZ55", "HZ56", "HZ57", "HZ58", "HZ59", "HZ60", "HZ61", "HZ62", "HZ63", "HZ64", "HZ65", "HZ66", "HZ67", "HZ68", "HZ69", "HZ70", "HZ71", "HZ72", "HZ73", "HZ74", "HZ75", "HZ76", "HZ77", "HZ78", "HZ79", "HZ80", "HZ81", "HZ82", "HZ83", "HZ84", "HZ85", "HZ86", "HZ87", "HZ88", "HZ89", "HZ90", "HZ91", "HZ92", "HZ93", "HZ94", "HZ95", "HZ96", "HZ97", "HZ98", "HZ99", "HZ100", "HZ101", "HZ102", "HZ103", "HZ104", "HZ105", "HZ106", "HZ107", "HZ108", "HZ110", "HZ111", "HZ113", "HZ114", "HZ115", "HZ116", "HZ117", "HZ118", "HZ119", "HZ120")
INSTALLA = Path("shared/volta/installa-herdr.sh")
HOOK = Path("hooks/herdr-stato.sh")
# Le opzioni che la scheda aggiunge al comando ssh dell'aggancio (argvScheda di sessioni.js, 11/11/2026):
# tetto alla connessione e battito, perché una connessione morta non tenga la scheda ferma.
OPZIONI_SSH = ["-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3"]
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
    if "shared/volta/installa-herdr.sh" not in passo:
        return "setup-herdr.md non lancia installa-herdr.sh"
    for parola in ("HERDR OK", "HERDR NO", "HERDR ERRORE"):
        if parola not in passo or (parola != "HERDR ERRORE" and parola not in (repo / INSTALLA).read_text(encoding="utf-8")):
            return f"l'esito {parola} non torna fra passo e script"
    # #5020: la firma locale si propone con una riga e il comando, e lo script è eseguibile come gli altri.
    if "HERDR FIRMA" not in passo:
        return "setup-herdr.md non dice cosa fare con la riga HERDR FIRMA"
    if not os.access(repo / "shared/volta/firma-locale.sh", os.X_OK):
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
    mod = repo / "shared/volta/mods/arturo"
    for js in mod.glob("*.js"):
        for rel in re.findall(r'from "\./([^"]+)"', js.read_text(encoding="utf-8")):
            if not (mod / rel).exists():
                return f"{js.name} importa {rel}, che non c'è"
    main = (mod / "main.js").read_text(encoding="utf-8")
    parti = set(re.findall(r"(\w+): \w+", re.search(r"const PARTI = \{(.*?)\};", main).group(1)))
    layout = (repo / "shared/volta/layouts/arturo.json").read_text(encoding="utf-8")
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
    dati = (repo / "shared/volta/mods/arturo/dati.js").read_text(encoding="utf-8")
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
    trova = (repo / "shared/volta/trova-progetti.md").read_text(encoding="utf-8")
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
    shutil.copyfile(repo / "shared/volta/mods/arturo/partenza.js", copia)
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
    mod = repo / "shared/volta/mods/arturo"
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
    mod = repo / "shared/volta/mods/arturo"
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
        return subprocess.run(["sh", str(repo / "shared/volta/arturo-app.sh"), *arg], capture_output=True,
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
            or (copia / "arturo-app.sh").read_bytes() != (repo / "shared/volta/arturo-app.sh").read_bytes():
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
    mod = repo / "shared/volta/mods/arturo"
    if "nota: Nota" not in (mod / "main.js").read_text(encoding="utf-8"):
        return "main.js non ha la parte nota"
    if json.loads((repo / "shared/volta/keys.json").read_text(encoding="utf-8")).get("global", {}).get("cmd-shift-n") != "arturo.nota":
        return "keys.json non lega cmd-shift-n alle note"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    # apriNota sta in comuni.js dal passo 3 di #5117: la usano la barra e l'elenco delle note.
    corpo = (mod / "comuni.js").read_text(encoding="utf-8").split("export async function apriNota(apri = null) {", 1)[-1].split("\n}\n", 1)[0]
    if 'else if (c === "nota") this.lungo(c, cx, () => apriNota(arg));' not in barra or corpo.find(" shot ") < 0 or corpo.find(" shot ") > corpo.find("openOverlay("):
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
    fonti = [f for f in (repo / "shared/volta").rglob("*") if f.is_file() and f.suffix in (".js", ".sh", ".py")]
    fonti.append(repo / "hooks/herdr-stato.sh")
    testi = [f.read_text(encoding="utf-8") for f in fonti]
    testi += [r for r in (repo / "hooks/session-start.sh").read_text(encoding="utf-8").splitlines() if "herdr" in r]
    # volta-immagini la parte Herdr la legge soltanto (volta_mod.py copia i WebP nell'app, 12/11/2026): la
    # scrive la config della persona, che la tiene in git apposta.
    return {m for testo in testi for m in re.findall(r"\.claude/data/([A-Za-z0-9_.-]+)", testo)} - SOLO_LETTI


SOLO_LETTI = {"volta-immagini"}


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
    env = dict(os.environ, HOME=str(casa), USERPROFILE=str(casa), SERVIZI_AGENTI=str(agenti), SERVIZI_NO_LAUNCHCTL="1")
    script = repo / "shared" / "volta" / "servizi-gui.sh"

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
    shutil.copyfile(repo / "shared/volta/mods/arturo/sessioni.js", copia)
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
        # una ferma senza trascrizione (nessun "chi") non si sa se chiede qualcosa: ti aspetta (#5366, HZ92)
        "dettaglio": ["Arturo · Ti aspetta da 3 ore", "Amaltea · Si è fermata con un errore"],
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
    mod = repo / "shared/volta/mods/arturo"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, dove in (('import { Volta } from "./volta.js";', "barra.js"), ("this.volta.init(cx);", "barra.js"),
                        ("this.volta.render(cx)", "barra.js"), ('else if (c === "volta") this.volta.premiId(arg, cx);', "barra.js")):
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
    volta = (repo / "shared/volta/mods/arturo/volta.js").read_text(encoding="utf-8")
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
    # di Volta, più ctrl-shift-c, -v e -f del terminale): Arturo non deve prenderne nessuno.
    sopra = casa / "sopra-herdr"
    (sopra / "app").mkdir(parents=True)
    (sopra / "app" / "keys.json").write_text(json.dumps({"global": {**dict.fromkeys(HERDR_CTRL, "herdr"), "ctrl-shift-t": "tab.new"}}), encoding="utf-8")
    r = installa(repo, sopra, "windows")
    if r.returncode != 0 or "lasciato com'era" in r.stdout:
        return f"su Windows un tasto di Arturo è già di Herdr: {r.stdout.strip()[-200:]}"
    if win.get("ctrl-shift-a") != "arturo.apri" or win.get("ctrl-shift-m") != "arturo.nota":
        return f"su Windows mancano Ctrl+Shift+A e Ctrl+Shift+M: {win}"
    voluti = {"ctrl-down": "arturo.volta-giro-avanti", "ctrl-up": "arturo.volta-giro-indietro", "ctrl-w": "arturo.volta-chiudi"}
    if {k: win.get(k) for k in voluti} != voluti:
        return f"su Windows Ctrl+↓, Ctrl+↑ e Ctrl+W non fanno quello che fanno ⌘↓, ⌘↑ e ⌘W sul Mac: {win}"
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
    mod = repo / "shared/volta/mods/arturo"
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
    if "if (!l.length) notify({ title: `Non trovo la sessione ${id}`" not in volta:
        return "premiId non avvisa quando la sessione non è nell'elenco"
    return None


def hz25(repo: Path, casa: Path) -> str | None:
    # Una finestra di dialogo chiusa ferma il suo codice al primo await: la chiusura viene dopo l'azione.
    mod = repo / "shared/volta/mods/arturo"
    prima = re.compile(r"(this\.chiudi\(\)|dopo\?\.\(\)|closeOverlay\([^)]*\));\s*(?:await\s+)?(apri|esegui|scrivi|chiedi|nuova|run)\(")
    for f in sorted(mod.glob("*.js")):
        m = prima.search(f.read_text(encoding="utf-8"))
        if m:
            return f"{f.name} chiude la finestra prima di {m.group(2)}(): l'azione non parte"
    attesi = {"suggerimenti.js": "else run(comandoSuggerimento(sug.id)); dopo?.(); })",
              "apri.js": "    if (r.tipo === \"sessione\") run(`arturo.volta-${chiaveSessione(r.s)}`);\n    else if (r.tipo === \"progetto\") run(comandoApri(slug(r.nome)));\n    else if (r.tipo === \"nuova\" && r.testo) run(comandoNuova(r.testo));\n    else return;\n    this.chiudi();",
              "revisione.js": ".on_click(() => { run(comandoApri(k)); this.chiudi(); })",
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
    mod = repo / "shared/volta/mods/arturo"
    main = (mod / "main.js").read_text(encoding="utf-8")
    if '"marchio", "barra", "piede", "testata", "schede", "todo", "stato", "benvenuto"' not in main \
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
    lay = (repo / "shared/volta/layouts/arturo.json").read_text(encoding="utf-8")
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
    mod = repo / "shared/volta/mods/arturo"
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
    vc = repo / "shared/volta"
    mod = vc / "mods/arturo"
    testo = {f: (mod / f).read_text(encoding="utf-8") for f in ("main.js", "barra.js", "testata.js", "noteui.js", "comuni.js")}
    for f, pezzo, perche in [
        ("main.js", "note: Note, casa: Casa,", "main.js non monta la parte note"),
        ("barra.js", 'else if (c === "note") apriElenco();', "il comando arturo.note non apre l'elenco"),
        ("barra.js", 'else if (c === "nota") this.lungo(c, cx, () => apriNota(arg));', "arturo.nota-<id> non apre il velo su quella nota"),
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
    if "# Note sulla finestra di Volta: 2 aperte" not in md or "`arturo note mostra 2026-11-10_07-00-00`" not in md:
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
    mod = repo / "shared/volta/mods/arturo"
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


# Due note aperte con lo stesso numero, nate su due macchine (volta_note.py, 12/11/2026): lo tiene la più vecchia.
DOPPIE = '[{"id": "x1", "numero": 1, "stato": "aperta", "progetto": "q", "quando": "2026-11-12T01:00:00Z"}, {"id": "x2", "numero": 1, "stato": "aperta", "progetto": "q", "quando": "2026-11-12T02:00:00Z"}, {"id": "x3", "numero": 2, "stato": "presa", "progetto": "q", "quando": "2026-11-12T03:00:00Z"}]'
NUMERI_DOPPIE = [["x1", 1], ["x2", 3], ["x3", 2]]

PROVA_FORMATO = r"""
const m = await import(%s);
const numeri = m.noteAperte(%s, "q").map((n) => [n.id, n.numero]).sort((a, b) => a[0].localeCompare(b[0]));
console.log(JSON.stringify({ tipi: Object.fromEntries(m.TIPI.map((x) => [x.id, x.etichetta])),
  predefinito: m.TIPO_PREDEFINITO, stati: m.STATI, aperte: [...m.APERTE], vuoto: m.VUOTO, numeri }));
"""

FORMATO_PY = r"""
import importlib.util, json, sys
s = importlib.util.spec_from_file_location("note_finestra", sys.argv[1])
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
sys.stdout.reconfigure(encoding="utf-8")  # il banco legge in UTF-8 anche su Windows (#5166)
numeri = sorted([n["id"], n["numero"]] for n in m.numerate(json.loads(sys.argv[2])) if n["stato"] in m.APERTE)
print(json.dumps({"tipi": m.TIPI, "predefinito": m.TIPO_PREDEFINITO, "stati": m.STATI,
                  "aperte": list(m.APERTE), "vuoto": m.VUOTO, "numeri": numeri}, ensure_ascii=False))
"""


def hz32(repo: Path, casa: Path) -> str | None:
    """Il formato di nota.json vive in due copie, nota.js del mod e bin/note_finestra.py: tipi, stati, stati
    aperti e dove vuoto devono dire lo stesso. L'aiuto e la guida nominano --chi e --json dei verbi."""
    aiuto = subprocess.run([sys.executable, str(repo / "bin/arturo"), "note", "aiuto"],  # il percorso vero, con l'UTF-8
                           capture_output=True, text=True, timeout=30).stdout
    guida = (repo / "docs/volta.md").read_text(encoding="utf-8")
    for dove, testo in (("l'aiuto di arturo note", aiuto), ("docs/volta.md", guida)):
        for pezzo in ("--chi", "--json"):
            if pezzo not in testo:
                return f"{dove} non spiega {pezzo}"
    if "dice a Federico" in guida:
        return "la guida parla a Federico invece che a chi usa Arturo"
    py = subprocess.run([sys.executable, "-c", FORMATO_PY, str(repo / "bin/note_finestra.py"), DOPPIE],
                        capture_output=True, text=True, timeout=30)
    if py.returncode != 0:
        return f"note_finestra.py non si carica: {(py.stderr or py.stdout).strip()[-160:]}"
    lato_py = json.loads(py.stdout)
    if lato_py["numeri"] != NUMERI_DOPPIE:
        return f"due note aperte con lo stesso numero: note_finestra.py dà {lato_py['numeri']}, la più nuova prende il primo libero"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(repo / "shared/volta/mods/arturo/nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_FORMATO % (json.dumps(copia.as_uri()), DOPPIE)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    lato_js = json.loads(r.stdout.strip().splitlines()[-1])
    diversi = [k for k in lato_js if lato_js[k] != lato_py.get(k)]
    if diversi:
        k = diversi[0]
        return f"nota.js e note_finestra.py non dicono lo stesso su {', '.join(diversi)}: {lato_js[k]} contro {lato_py.get(k)}"
    return None


# La riga di comandi.js che legge "volta-<id>": i comandi più lunghi con lo stesso inizio stanno prima.
CLIC_VOLTA = 'if (c.startsWith("volta-")) return { verbo: "volta",'


HERDR_FINTO = r"""
import { readFileSync, writeFileSync } from "node:fs";
export const lanciati = [];
export const appHome = () => process.env.HZ_APP;
export const home = () => process.env.HZ_CASA;
export const readTextFile = async (p) => { try { return readFileSync(p, "utf-8"); } catch { return null; } };
// writeTextFile come Herdr: scrive solo se il file è ancora quello atteso (null = nuovo); la cartella deve esserci.
export const scritti = [];
export const writeTextFile = async (p, testo, atteso) => {
  scritti.push([p, testo]);
  let ora = null;
  try { ora = readFileSync(p, "utf-8"); } catch { ora = null; }
  if (ora !== atteso) throw new Error("stale snapshot");
  writeFileSync(p, testo, "utf-8");
  return null;
};
export const eseguiti = [];
export const avvisi = [];
const condivisi = JSON.parse(process.env.HZ_SHARED || "{}");
export const nascite = [];
export const exec = async (cmd, args) => {
  eseguiti.push([cmd, ...args]);
  nascite.push(condivisi["arturo.nascita"] ?? null);
  // HZ_EXEC_CODICE e HZ_EXEC_ERR: il codice d'uscita e lo stderr, per chi legge l'esito (HZ73)
  if (process.env.HZ_EXEC_CODICE !== undefined)
    return { code: Number(process.env.HZ_EXEC_CODICE), stdout: process.env.HZ_EXEC ?? "", stderr: process.env.HZ_EXEC_ERR ?? "" };
  return process.env.HZ_EXEC ? { code: 0, stdout: process.env.HZ_EXEC, stderr: "" } : { code: 1, stdout: "", stderr: "" };
};
export const inviati = [];
// HZ_HC_GET: { <terminale>: [risposta, risposta, ...] } per hc get, una per chiamata (l'ultima resta).
const letture = JSON.parse(process.env.HZ_HC_GET || "{}");
const schermi = JSON.parse(process.env.HZ_HC_READ || "{}");
export const hc = async (a) => {
  inviati.push(a);
  const l = a[0] === "get" ? letture[a[1]] : null;
  if (l) return { code: 0, stdout: JSON.stringify(l.length > 1 ? l.shift() : l[0]), stderr: "" };
  // HZ_HC_READ: { <terminale>: schermo } per hc read
  if (a[0] === "read" && schermi[a[1]] !== undefined) return { code: 0, stdout: schermi[a[1]], stderr: "" };
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
  // HZ_CHIUDE: una scheda o un terminale chiuso sparisce, come in Herdr dopo tab.close e terminal.kill
  if (process.env.HZ_CHIUDE && (cmd === "tab.close" || cmd === "terminal.kill")) {
    const via = (finti.panes ?? []).filter((p) => (cmd === "tab.close" ? p.tab === a.id : p.terminal === a.terminal)).map((p) => p.terminal);
    if (cmd === "terminal.kill") via.push(a.terminal);
    finti.panes = (finti.panes ?? []).filter((p) => !via.includes(p.terminal));
    finti.terminals = (finti.terminals ?? []).filter((t) => !via.includes(t.address));
  }
  // HZ_NASCE: la scheda creata compare fra i terminali, come in Herdr dopo tab.new e space.new
  if (process.env.HZ_NASCE && (cmd === "tab.new" || cmd === "space.new") && a?.argv) {
    (finti.terminals ??= []).push({ address: process.env.HZ_NASCE, argv: a.argv });
    (finti.panes ??= []).push({ terminal: process.env.HZ_NASCE, tab: "tb-nuova" });
  }
};
"""

def mod_dati(repo: Path, mod: Path, dati: str) -> None:
    """dati.js per node: herdr finto, sessioni.js (puro) accanto come .mjs."""
    sessioni = (repo / "shared/volta/mods/arturo/sessioni.js").read_text(encoding="utf-8")
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
    dati = (repo / "shared/volta/mods/arturo/dati.js").read_text(encoding="utf-8")
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
    if not rimandi or not rimandi[0].is_file() or rimandi[0].resolve() != (repo / "shared/volta/trova-progetti.md").resolve():
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
    mod = repo / "shared/volta/mods/arturo"
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
    r = subprocess.run(["sh", str(repo / "shared/volta/volta-claude.sh"), *args],
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
    vc = repo / "shared/volta"
    home = casa / "home"
    home.mkdir()
    app = casa / "app"
    app.mkdir()
    (app / "volta-claude").write_text("#!/bin/sh\necho VOLTA \"$@\"\n", encoding="utf-8", newline="\n")
    os.chmod(app / "volta-claude", 0o755)
    prima = "export A=1\nalias ll='ls -l'"  # senza a capo in fondo
    (home / ".zshrc").write_text(prima, encoding="utf-8", newline="\n")
    (home / ".zshenv").write_text("claude() {\n  command claude \"$@\"\n}\n", encoding="utf-8", newline="\n")
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "SHELL": "/bin/zsh"}
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
    # un blocco senza la riga di fine (#5265): togli e metti non toccano il file e lo dicono; prima se ne
    # andava tutto quello che segue la riga di inizio, cioè il resto del .zshrc della persona
    monco = "export A=1\n# >>> Volta Celeste: le sessioni di claude nascono in background >>>\nvecchio\nalias ll='ls -l'\n"
    for verbo in ("togli", "metti"):
        (home / ".zshrc").write_text(monco, encoding="utf-8", newline="\n")
        r = nascita(verbo, str(app)) if verbo == "metti" else nascita(verbo)
        if (home / ".zshrc").read_text(encoding="utf-8") != monco:
            return f"{verbo} con un blocco senza la riga di fine cambia il .zshrc della persona"
        if "NASCITA SENZA FINE" not in r.stdout:
            return f"{verbo} con un blocco senza la riga di fine non lo dice: {r.stdout.strip()[-120:]}"
    (home / ".zshrc").write_text(prima + "\n", encoding="utf-8", newline="\n")
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
    env_i = {**os.environ, "HOME": str(sotto / "home"), "USERPROFILE": str(sotto / "home"), "SHELL": "/bin/zsh"}
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
    vc = repo / "shared/volta"
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
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "SHELL": "/bin/zsh", "VOLTA_PROFILI_PS": f"{p5}\n{p7}", "VOLTA_POLICY_PS": "RemoteSigned"}
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
    vc = repo / "shared/volta"
    app = casa / "app"
    app.mkdir()
    shutil.copy(vc / "nascita.sh", app / "volta-nascita.sh")
    env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "VOLTA_POLICY_PS": "RemoteSigned"}
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
    mod = repo / "shared/volta/mods/arturo"
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
        e = {**os.environ, "PATH": f"{fbin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(fcasa), "USERPROFILE": str(fcasa), "HERDR_APP_HOME": str(fapp)}
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
        if len(v["lanciati"]) != 1 or v["lanciati"][0].get("argv") != ["ssh", "-t", *OPZIONI_SSH, "torre.lan", "claude", "attach", "ffff1111"]:
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
        invii = lambda v: [x for x in v["inviati"] if x[0] == "send"]  # noqa: E731 (prima c'è hc get, HZ65)
        if v["avvisi"] or invii(v) != [["send", "t7", "Lavoriamo sul todo #42: Prova"]]:
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
        if v["eseguiti"] or len(invii(v)) != 1 or invii(v)[0][:2] != ["send", "t7"]:
            return f"Ricordami una cosa non scrive nella sessione agganciata aperta: {v['inviati']}, {v['eseguiti']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    if "nasceSu(t)" not in (mod / "testata.js").read_text(encoding="utf-8"):
        return "il benvenuto non mostra Nasce su, ma la sua Nuova richiesta la segue"
    # #5072: barra, testata e todo leggono lo stato di uno spazio da statoSpazio(), anche agganciato
    dj = (mod / "dati.js").read_text(encoding="utf-8")
    for file, pezzo in (("dati.js", "stato: statoSpazio(s)"), ("testata.js", "const st = statoScheda(s, tab);"), ("dati.js", "const volta = g && g.tab === tab?.id ? statoAgganciata(g) : null;"),
                        ("todo.js", "statoSpazio(spazio(p))"), ("todo.js", "    const st = statoSpazio(s);"),
                        ("barra.js", "`|${JSON.stringify(statiQui())}|")):  # la stella del marchio è ferma dal 13/11 (#5488)
        if pezzo not in (dj if file == "dati.js" else (mod / file).read_text(encoding="utf-8")):
            return f"{file} non legge lo stato di Volta per le sessioni agganciate: manca {pezzo}"
    return None



HC_FINTO_AZIONE = r"""import json, os, sys
with open(os.environ["HZ_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
print("stopped " + sys.argv[-1])
"""

# Un hc che esegue davvero il comando (#5555): come hc exec sul Mac, il PATH non ha ~/.local/bin, dove
# l'installatore mette claude. python3 è il Python del banco; un altro programma fuori dal PATH non parte.
HC_ESEGUE = r"""import json, os, shutil, subprocess, sys
a = sys.argv[1:]
if "--timeout" in a[:6]:
    i = a.index("--timeout"); del a[i:i + 2]
with open(os.environ["HZ_HC_LOG"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(a) + "\n")
env = dict(os.environ, PATH="/usr/bin:/bin", HOME=os.environ["HZ_CASA"])
prog = sys.executable if a[3] == "python3" else shutil.which(a[3], path=env["PATH"])
if a[:2] != ["exec", "--on"] or prog is None:
    print(json.dumps({"error": {"kind": "spawn_failed", "message": "cannot start %s: No such file or directory" % a[3]}})); sys.exit(1)
sys.exit(subprocess.call([prog] + a[4:], env=env))
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
    mod = repo / "shared/volta/mods/arturo"
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
        # sul Mac claude sta in ~/.local/bin, fuori dal PATH di hc exec (#5555): la sonda lo trova lo stesso
        mcasa = casa / "mcasa"
        (mcasa / ".local/bin").mkdir(parents=True)
        shutil.copyfile(bindir / "claude", mcasa / ".local/bin/claude")
        os.chmod(mcasa / ".local/bin/claude", 0o755)
        (casa / "hc_esegue.py").write_text(HC_ESEGUE, encoding="utf-8")
        hlog = casa / "hc.log"
        hlog.write_text("", encoding="utf-8")
        log.write_text("", encoding="utf-8")
        r = az("Mac", "stop", "abcd1234", VOLTA_HC=json.dumps([sys.executable, str(casa / "hc_esegue.py")]),
               HZ_HC_LOG=str(hlog), HZ_CASA=str(mcasa))
        gesti = [json.loads(x)[3] for x in hlog.read_text(encoding="utf-8").splitlines() if x.strip()]
        fine = json.loads((r.stdout.strip().splitlines() or ["{}"])[-1])
        if fine.get("ok") is not True or fine.get("testo") != "stop ok" or gesti != ["claude", "python3"]:
            return f"stop sul Mac senza claude nel PATH di hc exec: {fine}, hc ha lanciato {gesti}, {r.stderr.strip()[-120:]}"
        if log.read_text(encoding="utf-8").split() != ["stop", "abcd1234"]:
            return f"il claude di ~/.local/bin non ha ricevuto stop abcd1234: {log.read_text(encoding='utf-8')!r}"
    node = shutil.which("node")
    if node:
        copia = casa / "sessioni.mjs"
        shutil.copyfile(mod / "sessioni.js", copia)
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_GESTI % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
        d = json.loads(r.stdout.strip().splitlines()[-1])
        attesi = {"lavora": ["logs", "stop"], "aspetta": ["logs", "stop"], "ferma": ["logs"], "errore": ["logs", "respawn", "rm!"],
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
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    nata = {"id": "ffff1111", "sessionId": "ffff1111-aaaa", "claude": "C:/u/claude.exe", "cartella": "C:/u/ClaudeCode"}
    conf = {
        "macchine": [{"name": n, "target": n.lower(), "state": "connected"} for n in ("Torre", "Win", "Rotto", "Muto", "Mac", "Mela", "Storto")],
        "exec": {"Torre": {"python": nata}, "Win": {"python": nata, "claude": "respawned ffff1111"},
                 "Mac": {"python3": "respawned ffff1111"},
                 "Rotto": {"python3": nata, "claude": "respawned ffff1111"}, "Muto": {"python3": nata},
                 "Mela": {"python3": nata}, "Storto": {"python3": nata}},
        "servizio": {"Win": {"serve": "hc-run"}, "Rotto": {"errore": "Claude Code non c'è su questa macchina"},
                     "Muto": {"serve": "hc-run"}, "Mela": {"serve": "hc-run", "claude": "/Users/u/.local/bin/claude"},
                     "Storto": {"serve": "hc-run", "claude": "/bin/sh"}},
        "dopo_run": {n: {"acceso": True, "come": "già acceso"} for n in ("Win", "Mela", "Storto")},
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
    # un Mac senza LaunchAgent (#5560): il terminale di herdr-core non ha ~/.local/bin nel PATH
    for nome, atteso in (("Mela", "/Users/u/.local/bin/claude"), ("Storto", "claude")):
        rc, d, ch = lancia("servizio", nome)
        corsa = [c[c.index("--bg") + 1] for c in ch if c[:1] == ["run"]]
        if rc != 0 or d.get("come") != "terminale di Herdr" or corsa != [atteso]:
            return f"servizio su {nome} con hc run: rc {rc}, {d}, lancia {corsa}, atteso {atteso}"
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
    # sul Mac hc exec non trova claude nel PATH (#5555): Riavvia riprova con python3, che lo cerca in ~/.local/bin
    rc, d, ch = lancia("azione", "Mac", "respawn", "ffff1111")
    gesti = [c[3] for c in ch if c[:2] == ["exec", "--on"] and c[-1] != "remoto"]
    if rc != 0 or d.get("ok") is not True or gesti != ["claude", "python3"] or ch[-1][-2:] != ["respawn", "ffff1111"]:
        return f"Riavvia sul Mac senza claude nel PATH di hc exec: rc {rc}, {d}, {ch}"
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
    e = {**os.environ, "PATH": f"{fbin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(fcasa), "USERPROFILE": str(fcasa), "HZ_LOG": str(slog)}
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
    if sys.platform == "darwin":  # chiesto da un'altra macchina, senza LaunchAgent: il percorso intero (#5560)
        r = subprocess.run([sys.executable, "-c", importlib_spec("volta_sonda_hz41", sonda).SERVIZIO, "remoto"], capture_output=True, text=True, timeout=60, env=e)
        d = json.loads(r.stdout.strip().splitlines()[-1])
        if d != {"serve": "hc-run", "claude": str(fc)}:
            return f"SERVIZIO remoto su un Mac senza LaunchAgent: {d}, atteso il percorso {fc}"
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
    mod = repo / "shared/volta/mods/arturo"
    sonda = mod / "volta_sonda.py"
    import ast  # noqa: PLC0415
    costanti = {n.targets[0].id: n.value.value for n in ast.parse(sonda.read_text(encoding="utf-8")).body
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id.startswith("ATTESA_") and isinstance(n.value, ast.Constant)}
    if set(costanti) != {"ATTESA_MACCHINE", "ATTESA_SERVIZIO", "ATTESA_NASCITA", "ATTESA_AZIONE", "ATTESA_LETTURA"}:
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
    vc = repo / "shared/volta"
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
    mod = repo / "shared/volta/mods/arturo"
    bj = (mod / "barra.js").read_text(encoding="utf-8")
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    cj = (mod / "comandi.js").read_text(encoding="utf-8")
    altro, gesto, clic = cj.find('c.startsWith("volta-altro-")'), cj.find("/^volta-gesto-([a-z]+)-(.+)$/.exec(c)"), cj.find(CLIC_VOLTA)
    if min(altro, gesto) < 0 or clic < 0 or max(altro, gesto) > clic:
        return "comandi.js non legge volta-altro- e volta-gesto- prima di volta-<id>"
    if "this.volta.altroId(arg, cx)" not in bj or "this.volta.gestoId(arg.verbo, arg.id, cx)" not in bj:
        return "barra.js non passa i comandi ad altroId e gestoId"
    if "this.menu = chiave(s);\n    this.scopri(s);\n    this.fare(s, a, cx);" not in vj or "this.menu = this.menu === chiave(s) ? null : chiave(s);\n    this.scopri(s);" not in vj:
        return "volta.js: gestoId non preme il bottone, o altroId non apre e chiude Altro"
    if 'if (g && s.stato === "ferma") this.aperti[g.chiave] = true;' not in vj:
        return "volta.js: il comando non apre il gruppo delle ferme, e la sessione resta nascosta"
    bindir = casa / "bin"
    bindir.mkdir()
    if os.name == "nt":
        # su Windows lo shebang non vale: shutil.which della sonda trova claude.cmd, che lancia lo script
        (bindir / "claude.py").write_text(CLAUDE_FINTO_ELENCO, encoding="utf-8")
        (bindir / "claude.cmd").write_text(f'@"{sys.executable}" "%~dp0claude.py" %*\r\n', encoding="utf-8")
    else:
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
    mod = repo / "shared/volta/mods/arturo"
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
    if 'setShared("arturo.volta.gruppi", arg)' not in (mod / "barra.js").read_text(encoding="utf-8"):
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
    mod = repo / "shared/volta/mods/arturo"
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
    vj = (repo / "shared/volta/mods/arturo/volta.js").read_text(encoding="utf-8")
    inizio, fine = vj.find("  pannello(t) {"), vj.find("  riga(t, s, modo, cx) {")
    if inizio < 0 or fine < inizio:
        return "volta.js non ha pannello() prima di riga()"
    corpo = vj[inizio:fine]
    if vj.count("this.gesti(t, s, az)") != 1 or "this.gesti(t, s, az)" not in corpo:
        return "volta.js: i gesti non stanno solo nel pannello (una riga in fondo li apre sotto il bordo)"
    for pezzo in ("chiave(x) === this.menu", "child(titolo(s))", "this.menu = null; cx.notify();", "child(avviso)"):
        if pezzo not in corpo:
            return f"volta.js: al pannello dei gesti manca {pezzo}"
    elenco = vj.find('.id("volta-elenco").flex_1().min_h(0).overflow_y_scroll()')
    fuori = vj.find("const gesti = this.pannello(t);")
    dopo = vj.find(".child(corpo)\n      .when(Boolean(gesti), (el) => el.child(gesti.mb(10)));")
    if min(elenco, fuori, dopo) < 0 or not elenco < fuori < dopo:
        return "volta.js: il pannello dei gesti non sta sotto l'elenco, fuori dalla parte che scorre"
    if ".when(Boolean(avviso) && !aperto, (el)" not in vj[fine:]:
        return "volta.js: con Altro aperto l'avviso del gesto esce due volte, nella riga e nel pannello"
    return None


def hz48(repo: Path, casa: Path) -> str | None:
    import importlib.util
    sp = importlib.util.spec_from_file_location("volta_sonda_hz48", repo / "shared/volta/mods/arturo/volta_sonda.py")
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
    vj = (repo / "shared/volta/mods/arturo/volta.js").read_text(encoding="utf-8")
    inizio, fine = vj.find("  riga(t, s, modo, cx) {"), vj.find("  interruttore(t) {")
    if inizio < 0 or fine < inizio:
        return "volta.js non ha riga() prima di interruttore()"
    corpo = vj[inizio:fine]
    for pezzo, perche in (("const xa = xRiga(s);", "la X non nasce da xRiga() di sessioni.js"),
                          ("const vediX = Boolean(xa) && (this.sopra === k || chiedoX || faccioX);", "la X non segue il puntatore"),
                          (".when(!vediX, (el) => el.invisible())", "la X nascosta non tiene il suo posto"),
                          (".on_click((_e, cx) => this.fare(s, xa, cx))", "il clic sulla X non passa da fare() con la conferma"),
                          ('ICONA("x")', "manca l'icona x"),
                          (".on_hover((h, cx) =>", "la riga non segue il puntatore"),
                          (".when(Boolean(x), (el) => el.child(x))", "la riga non mostra la X")):
        if pezzo not in corpo:
            return f"volta.js: {perche} ({pezzo})"
    if "this.sopra = null;" not in vj[:inizio]:
        return "volta.js: init non prepara this.sopra"
    return None


def hz50(repo: Path, casa: Path) -> str | None:
    bj = (repo / "shared/volta/mods/arturo/barra.js").read_text(encoding="utf-8")
    piede = bj[bj.find("export class Piede {"):]
    if 'pulsanteIcona("note", "pin", `Note · ${tasti().nota} nuova · ${tasti().elenco} elenco`, () => apriElenco()' not in piede:
        return "barra.js: il piede non ha l'icona Note che apre l'elenco delle note"
    if "${tasti().nota} nuova · ${tasti().elenco}" not in piede:
        return "barra.js: la voce Note non scrive i tasti della nota nuova e dell'elenco"
    lay = json.loads((repo / "shared/volta/layouts/arturo.json").read_text(encoding="utf-8"))
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
    attesa = piede_misure(repo)
    if attesa is None or alti != [attesa]:
        return f"layout arturo: il piede è alto {alti}, misure.js vuole PIEDE = {attesa}"
    return None


def piede_misure(repo: Path) -> int | None:
    """L'altezza del piede scritta in misure.js (export const PIEDE = N;), o None."""
    m = re.search(r"^export const PIEDE = (\d+);$", (repo / "shared/volta/mods/arturo/misure.js").read_text(encoding="utf-8"), re.M)
    return int(m.group(1)) if m else None


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
    mod = repo / "shared/volta/mods/arturo"
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
else if (caso === "comando-win") esito = comando([String.raw`C:\Windows\System32\OpenSSH\ssh.exe`, "-t", "h", "/a b/claude", "attach", "x'y"]);
else {
  const s = { id: "ffff1111", sessionId: "ffff1111-aaaa", host: "Torre", macchina: "Torre", nome: "Progetto x", progetto: "progetto-x",
              stato: process.env.HZ_STATO || "ferma", tipo: "background" };
  const r = await apriSessione(s, process.env.HZ_ATTACH ? JSON.parse(process.env.HZ_ATTACH) : ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"],
                               process.env.HZ_PRONTA === "1");
  veglia = r.veglia ? await r.veglia : null;
  esito = { ...r, veglia: undefined };
}
console.log(JSON.stringify({ lanciati, eseguiti, avvisi, inviati, esito, veglia, etichetta: ETICHETTA }));
"""


def hz52(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    mod = repo / "shared/volta/mods/arturo"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_APRI, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    attach = ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]
    riga = "ssh -t %s torre.lan claude attach ffff1111" % " ".join(OPZIONI_SSH)
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
        for k in ("HZ_NASCE", "HZ_STATO", "HZ_PRONTA", "HZ_HC_ROTTO", "HZ_HC_READ", "HZ_ATTACH"):
            if k not in extra:
                e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=30, env=e)
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
        # l'etichetta è la chiave macchina:id dal 14/11/2026 (#5634)
        if ["label", "t7", f"{v['etichetta']}=Torre:ffff1111"] not in v["inviati"] or v["etichetta"] != "arturo.sessione":
            return f"la scheda ritrovata per argv non riceve l'etichetta: {v['inviati']}"
        # ritrovata per etichetta, anche se l'argv non dice niente e il nome è un altro
        etichettata = {**herdr, "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": ["zsh"], "labels": {"arturo.sessione": "Torre:ffff1111"}}]}
        v = volta(herdr=etichettata, letture={"t7": [viva]})
        if v["esito"].get("come") != "davanti" or nuove(v) or any(x[0] == "label" for x in v["inviati"]):
            return f"una scheda con l'etichetta non si ritrova, o si rietichetta: {v['esito']}, {v['inviati']}"
        # un'etichetta di prima del 14/11 col solo id si ritrova e passa alla chiave macchina:id (#5634)
        vecchia = {**herdr, "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": ["zsh"], "labels": {"arturo.sessione": "ffff1111"}}]}
        v = volta(herdr=vecchia, letture={"t7": [viva]})
        if v["esito"].get("come") != "davanti" or nuove(v) or ["label", "t7", "arturo.sessione=Torre:ffff1111"] not in v["inviati"]:
            return f"una scheda con l'etichetta vecchia non si ritrova, o non passa alla chiave: {v['esito']}, {v['inviati']}"
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
        if len(nuove(v)) != 1 or nuove(v)[0].get("argv") != attach[:2] + OPZIONI_SSH + attach[2:] or sonda(v) != [["apri", "Torre", "ffff1111"]]:
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
        if v["veglia"] != {"riavviata": True} or ["label", "t9", "arturo.sessione=Torre:ffff1111"] not in v["inviati"]:
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
        # Windows (12/11/2026, volta cff2611): la shell della scheda è PowerShell. comando() scrive & e gli apici
        # di PowerShell (' raddoppiato); gli apici di sh davano ParserError "Token imprevisto '-t'".
        ssh_win = r"C:\Windows\System32\OpenSSH\ssh.exe"
        v = volta("comando-win")
        if v["esito"] != "& '%s' '-t' 'h' '/a b/claude' 'attach' 'x''y'" % ssh_win:
            return f"comando() su Windows non scrive per PowerShell: {v['esito']}"
        # Windows: foreground.argv[0] è il percorso intero di pwsh, l'argv della scheda dice "pwsh.exe". Nuda la
        # decide lo schermo (hc read): Claude acceso va davanti senza scrivere niente, il prompt PS rilancia.
        attach_win = [ssh_win, "-t", "torre.lan", "claude", "attach", "ffff1111"]
        nascita_win = ["pwsh.exe", "-NoExit", "-Command", "& " + " ".join("'%s'" % x for x in attach_win)]
        get_win = {"state": "live", "pid": 10, "argv": nascita_win,
                   "foreground": {"pid": 10, "argv": [r"C:\Program Files\PowerShell\7\pwsh.exe"] + nascita_win[1:]}}
        herdr_win = {**herdr, "terminals": [{"address": "t3", "argv": ["pwsh.exe"]},
                                            {"address": "t7", "argv": nascita_win, "labels": {"arturo.sessione": "ffff1111"}}]}
        acceso = "Fatto.\n\u276f \n  Opus5.5 \u2502 ClaudeCode 12%\n"
        v = volta(herdr=herdr_win, letture={"t7": [get_win]}, HZ_ATTACH=json.dumps(attach_win), HZ_HC_READ=json.dumps({"t7": acceso}))
        if v["esito"].get("come") != "davanti" or invii(v):
            return f"Windows: una scheda pwsh con Claude acceso riceve l'aggancio dentro Claude: {v['esito']}, {invii(v)}"
        prompt = "Session ffff1111 has exited.\n" + r"PS C:\Users\x>" + "\n"
        v = volta(herdr=herdr_win, letture={"t7": [get_win]}, HZ_ATTACH=json.dumps(attach_win), HZ_HC_READ=json.dumps({"t7": prompt}))
        riga_win = "& " + " ".join("'%s'" % x for x in [ssh_win, "-t", *OPZIONI_SSH, "torre.lan", "claude", "attach", "ffff1111"])
        if v["esito"].get("come") != "rilanciata" or not invii(v) or invii(v)[0] != ["send", "t7", riga_win]:
            return f"Windows: il prompt PS non rilancia l'aggancio scritto per PowerShell: {v['esito']}, {invii(v)[:1]}"
        # la scheda nuova: una sessione senza prompt nel progetto dello spazio aperto
        v = volta("nuova-scheda", herdr=omonima, uscita=json.dumps({"id": "ffff1111", "sessionId": "ffff1111-aaaa", "attach": attach}))
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["nasci", "qui", "--progetto", "progetto-x", "--", "/inizio progetto-x"]:
            return f"la scheda nuova non fa nascere una sessione nel progetto aperto, partita da /inizio (#5465): {v['eseguiti'][:1]}"
        if len(nuove(v)) != 1 or nuove(v)[0].get("name") != "Nuova sessione" or nuove(v)[0].get("space") != "s1" or nuove(v)[0].get("argv") != attach[:2] + OPZIONI_SSH + attach[2:]:
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
    for pezzo in ("this.apro[k] = true;", "if (r.errore) this.nonApre(s, r.errore, cx);", "if (v?.errore) this.nonApre(s, v.errore, cx);",
                  "this.apri({ ...s, id: portata.id ?? s.id }, portata.attach, true, cx);", '{ testo: "La apro…", colore: "working" }'):
        if pezzo not in vj:
            return f"volta.js senza {pezzo}"
    return None


def hz53(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
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
    # i tasti: ⌘T apre le tessere dei progetti (HZ96), la cui prima tessera è la sessione nuova di Claude
    vc = repo / "shared/volta"
    if leggi(vc / "keys.json").get("global", {}).get("cmd-t") != "arturo.casa":
        return "keys.json non lega cmd-t alle tessere di Volta"
    if leggi(vc / "keys-ctrl.json").get("global", {}).get("ctrl-shift-t") != "arturo.casa":
        return "keys-ctrl.json non lega ctrl-shift-t alle tessere di Volta"
    for nome, prima, atteso in (("di Herdr", "tab.new", "arturo.casa"), ("della Volta di prima", "arturo.volta-nuova", "arturo.casa"),
                                ("della persona", "pane.split:right", "pane.split:right")):
        sotto = casa / f"tasti-{prima[:9].replace(':', '-')}"
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
    if 'else if (c === "volta-nuova") this.lungo(c, cx, () => nuovaScheda());' not in barra:
        return "barra.js non porta arturo.volta-nuova a nuovaScheda()"
    cj = (mod / "comandi.js").read_text(encoding="utf-8")
    if cj.index('c === "volta-nuova"') > cj.index(CLIC_VOLTA):
        return "comandi.js: volta-nuova finisce nel clic su una sessione, che viene prima"
    return None


PROVA_MENU = """
import * as m from %s;
const bg = (stato, altro = {}) => ({ tipo: "background", stato, host: "qui", sessionId: "s-" + stato, id: stato.slice(0, 4), ...altro });
const verbi = (s) => m.menu(s).map((a) => a.verbo + (a.conferma ? "!" : ""));
console.log(JSON.stringify({
  lavora: verbi(bg("lavora")), ferma: verbi(bg("ferma")), errore: verbi(bg("errore")),
  interattiva: verbi({ ...bg("ferma"), tipo: "interattiva" }), vecchia: verbi(bg("ferma", { vecchia: true })), niente: verbi(null),
  conProgetto: verbi(bg("lavora", { progetto: "deck" })),
  x: [m.xRiga(bg("lavora")), m.xRiga(bg("errore")), m.xRiga({ ...bg("ferma"), tipo: "interattiva" }), m.xRiga(bg("ferma", { vecchia: true }))].map((a) => a ? a.verbo + (a.conferma ? "!" : "") : null),
  testi: m.menu(bg("errore")).filter((a) => a.verbo !== "respawn").map((a) => a.testo), solo: [...m.SOLO_MENU].sort(),
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
    mod = repo / "shared/volta/mods/arturo"
    testi = {n: (mod / n).read_text(encoding="utf-8") for n in ("volta.js", "barra.js", "main.js", "menusessione.js", "dati.js")}
    attesi = (
        ("volta.js", '.on_mouse_down("right", (_e, cx) => { if (apriMenuSessione(s)) cx.stop_propagation(); })', "il tasto destro non apre il menu"),
        ("volta.js", "if (SOLO_MENU.has(verbo)) return this.fare(s, a, cx);", "un gesto del solo menu apre il riquadro di Altro"),
        ("volta.js", 'if (a.verbo === "apri") return this.premi(s, cx);', "Apri non è il clic sulla sessione"),
        ("volta.js", '    chiudiSchede(s);\n    this.congeda(s, cx);', "Chiudi non chiude la scheda prima del congedo (HZ89)"),
        ("volta.js", 'a.verbo === "duplica" || a.verbo === "fork" ? await copiaSessione(s, a.verbo)', "Duplica e Fork non passano da copiaSessione"),
        ("volta.js", ': lavoro ? { testo: lavoro, colore: "working" }', "la riga non dice che il gesto è in corso"),
        ("volta.js", "const voci = menu(s).concat(", "gestoId non conosce le voci del menu"),
        ("barra.js", 'else if (c === "volta-menu") this.volta.menuId(arg);', "barra.js non apre il menu da comando"),
        ("main.js", "sessione: MenuSessione,", "main.js non monta il menu di una sessione"),
        ("menusessione.js", 'openOverlay({ mod: "arturo", props: { parte: "sessione", sessione: s }, kind: "popup"', "il menu non è un popup del mod"),
        ("menusessione.js", "    run(comandoGesto(this.s, v));\n    this.chiudi();", "il menu si chiude prima di mandare il gesto"),
        ("menusessione.js", "`arturo.volta-gesto-${v.verbo}-${chiaveSessione(s)}`", "il menu non manda il comando che barra.js legge"),
        ("menusessione.js", "this.voci = menu(this.s);", "le voci del menu non vengono da menu() di sessioni.js"),
    )
    for file, pezzo, motivo in attesi:
        if pezzo not in testi[file]:
            return f"{file}: {motivo}"
    cj = (mod / "comandi.js").read_text(encoding="utf-8")
    if cj.index('c.startsWith("volta-menu-")') > cj.index(CLIC_VOLTA):
        return "comandi.js: volta-menu-<id> finisce nel clic su una sessione, che viene prima"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "sessioni.mjs"
    shutil.copyfile(mod / "sessioni.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_MENU % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    # 12/11/2026 notte: copiare e spostare (Sposta in un progetto è il "taglia", Sposta su… un'altra macchina,
    # caso HZ104), poi nome e contesto, poi Chiudi con /fine (non su una in errore: lì c'è Elimina); la X
    # della riga viene da xRiga()
    primi = ["apri", "duplica", "fork", "progetto"]
    voci = {"lavora": [*primi, "sposta", "rinomina", "chiudi", "logs"], "ferma": [*primi, "sposta", "rinomina", "chiudi", "logs"],
            "errore": [*primi, "sposta", "rinomina", "logs", "respawn", "rm!"], "interattiva": [*primi, "rinomina"],
            "conProgetto": [*primi, "sposta", "rinomina", "contesto", "chiudi", "logs"],
            "vecchia": [], "niente": [], "testi": ["Apri", "Duplica", "Fork", "Sposta in un progetto…", "Sposta su…", "Rinomina…", "Anteprima", "Elimina"],
            "solo": ["apri", "chiudi", "contesto", "duplica", "fork", "progetto", "rinomina", "sposta"], "fork": ["Rifare il deck (fork)", 60],
            "x": ["chiudi!", "rm!", None, None]}
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
        if len(nuove(v)) != 1 or nuove(v)[0].get("argv") != attach[:2] + OPZIONI_SSH + attach[2:] or nuove(v)[0].get("name") != "Rifare il deck (fork)" or nuove(v)[0].get("space") != "s1":
            return f"la copia non si aggancia nello spazio del progetto col suo nome: {nuove(v)}"
        if v["esito"] != {"ok": True, "id": "eeee2222"} or v["avvisi"]:
            return f"Fork riuscito: esito {v['esito']}, avvisi {v['avvisi']}"
        v = volta("duplica")
        if not v["eseguiti"] or v["eseguiti"][0][2:] != ["duplica", "Torre", "--progetto", "Progetto X", "--cartella", "/lavori/x", "--", "/inizio Progetto X"]:
            return f"Duplica non chiama la sonda sulla macchina della sessione, nella sua cartella, partita da /inizio (#5465): {v['eseguiti'][:1]}"
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
        if v["esito"] != 2 or chiuse != sorted(json.dumps(x, sort_keys=True) for x in ({"cmd": "tab.close", "id": "tb1", "confirmed": True}, {"cmd": "terminal.kill", "terminal": "t8"})):
            return f"Chiudi non chiude la scheda sola e il solo terminale di quella divisa: {v['esito']}, {v['lanciati']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    return None


def hz55(repo: Path, casa: Path) -> str | None:
    import base64  # noqa: PLC0415
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
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
    locale = {"PATH": f"{fbin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(fcasa), "USERPROFILE": str(fcasa), "HERDR_APP_HOME": str(fapp)}

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


# I file che Herdr scrive da sé nella cartella di un mod aperto in un editor: fuori da git e da ORIGINE.
GENERATI_DA_HERDR = ("gpui-kit.d.ts", "herdr.d.ts", "jsconfig.json")

PROVA_RIGA_MOD = """
import * as m from %s;
const ora = new Date(2026, 10, 11, 12, 0, 0).getTime();
const t = (h, mi, g = 11) => new Date(2026, 10, g, h, mi, 0).getTime() / 1000;
console.log(JSON.stringify({
  niente: m.rigaMod(null),
  oggi: m.rigaMod({ corta: "abc1234", installato: t(9, 5) }, ora),
  ieri: m.rigaMod({ corta: "abc1234", installato: t(18, 30, 10) }, ora),
  giu: m.rigaMod({ corta: "abc1234", installato: t(9, 5), esito: "errore", giu_da: ora / 1000 - 3 * 86400 - 5, motivo: "rete" }, ora),
  giuDaPoco: m.rigaMod({ corta: "abc1234", installato: t(9, 5), esito: "errore", giu_da: ora / 1000 - 3600 }, ora),
  bloccato: m.rigaMod({ corta: "abc1234", installato: t(9, 5), programmi: { plugin: { esito: "compromesso", motivo: "tag senza firma" } } }, ora),
  pluginOk: m.rigaMod({ corta: "abc1234", installato: t(9, 5), programmi: { plugin: { esito: "aggiornato" } } }, ora),
}));
"""


def hz56(repo: Path, casa: Path) -> str | None:
    import hashlib  # noqa: PLC0415
    vc = repo / "shared/volta"
    try:
        attesi = json.loads((vc / "ORIGINE").read_text(encoding="utf-8"))["file"]
    except (OSError, ValueError, KeyError):
        return "shared/volta/ORIGINE manca o non si legge: la copia la scrive volta/pubblica-mod.py"
    veri = {str(f.relative_to(vc)).replace(os.sep, "/"): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in vc.rglob("*") if f.is_file() and f.name not in ("ORIGINE",) + GENERATI_DA_HERDR and "__pycache__" not in f.parts}
    diversi = sorted(k for k in set(attesi) | set(veri) if attesi.get(k) != veri.get(k))
    if diversi:
        return f"shared/volta non è la copia di ORIGINE (la fonte è il repository di Volta): {diversi[:4]}"
    return None


def hz57(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta"
    mod = vc / "mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ("const script = `${appHome()}/volta_mod.py`;", "if (controlloMod || !(await esiste(script))) return;",
                  'await exec(py, [script, "controlla"], { timeout: 300000 });', 'setShared("arturo.mod", {',
                  "      controllaMod(this.py);\n      const sc = await script(c);",
                  "cx.timer.every(OGNI_MOD, () => controllaMod(this.py));"):
        if pezzo not in vj:
            return f"volta.js non chiede il controllo del mod: manca {pezzo}"
    bj = (mod / "barra.js").read_text(encoding="utf-8")
    cj = (mod / "comuni.js").read_text(encoding="utf-8")
    menu = cj[cj.find("export class Impostazioni {"):cj.find("export function segnaleImpostazioni")]
    if '.when(Boolean(rigaMod(shared("arturo.mod"))), (el) =>' not in menu or 'else if (c === "versione")' not in bj:
        return "comuni.js: il menu di Impostazioni non scrive la versione del mod, o manca il comando arturo.versione"
    if '`Impostazioni · ${rigaMod(shared("arturo.mod"))?.testo ?? tasti().impostazioni}`' not in bj[bj.find("export class Piede {"):]:
        return "barra.js: l'icona di Impostazioni non porta la versione del mod nel suggerimento"
    if f'"id": "piede", "type": "block", "size": {{"px": {piede_misure(repo)}}}' not in json.dumps(json.loads((vc / "layouts/arturo.json").read_text(encoding="utf-8"))):
        return "il piede non è alto PIEDE di misure.js: la versione sta nel menu di Impostazioni proprio per non aggiungere righe"
    sonda = (vc / "volta_mod.py").read_text(encoding="utf-8")
    for pezzo in ('if not isinstance(url, str) or not url:', 'motivo, rosso = controlla_mod(nuovo)', 'c.get("mod_modo") == "manuale"'):
        if pezzo not in sonda:
            return f"volta_mod.py: manca {pezzo}"
    node = shutil.which("node")
    if node:
        copia = casa / "sessioni.mjs"
        shutil.copyfile(mod / "sessioni.js", copia)
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_RIGA_MOD % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
        d = json.loads(r.stdout.strip().splitlines()[-1])
        attesa = {"niente": None, "oggi": {"testo": "mod abc1234 · 09:05"}, "ieri": {"testo": "mod abc1234 · 10/11 18:30"},
                  "giu": {"testo": "mod abc1234 · non controllo da 3 giorni", "avviso": "rete"}, "giuDaPoco": {"testo": "mod abc1234 · 09:05"},
                  "bloccato": {"testo": "mod abc1234 · Arturo non si aggiorna", "avviso": "tag senza firma"},
                  "pluginOk": {"testo": "mod abc1234 · 09:05"}}
        if d != attesa:
            return f"rigaMod: {d}"
    return None


def hz58(repo: Path, casa: Path) -> str | None:
    import base64  # noqa: PLC0415
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    radice, log, uscita = casa / "conf", casa / "log", casa / "scheda.out"
    (radice / "cache").mkdir(parents=True)
    log.write_text("", encoding="utf-8")
    sid = "aaaa1111-2222-3333-4444-555555555555"
    conf = {"macchine": [{"name": "Torre", "target": "torre.lan", "state": "connected"}],
            "exec": {"Torre": {"python3": {"ok": True, "titolo": "Nome mio", "portato": False}}}}
    finto = casa / "hc_finto.py"
    finto.write_text(HC_FINTO, encoding="utf-8")
    hclog = casa / "hc.log"
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(radice), "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)]),
           "HZ_HC_LOG": str(hclog), "HZ_LOG": str(log), "PYTHONIOENCODING": "utf-8", "ARTURO_SCHEDA_USCITA": str(uscita)}
    for k in ("ARTURO_TITOLI", "ARTURO_TITOLO_FIGLIO", "ARTURO_TITOLI_OGNI"):
        env.pop(k, None)

    def lancia(*args):
        hclog.write_text("", encoding="utf-8")
        r = subprocess.run([sys.executable, str(sonda), *args], capture_output=True, text=True, timeout=90, env=env)
        chiamate = [json.loads(x) for x in hclog.read_text(encoding="utf-8").splitlines() if x.strip()]
        try:
            return r.returncode, json.loads(r.stdout.strip().splitlines()[-1]), chiamate
        except (ValueError, IndexError):
            return r.returncode, {"uscita": (r.stderr or r.stdout).strip()[-160:]}, chiamate

    titolo, scheda = radice / "cache" / "titolo" / f"{sid}.json", radice / "cache" / "scheda" / f"{sid}.json"
    rc, d, _ = lancia("rinomina", "qui", sid, "--", "Nome  mio\tdella sessione")
    t = leggi(titolo) if titolo.exists() else {}
    if rc != 0 or d != {"ok": True, "titolo": "Nome mio della sessione", "portato": False}:
        return f"rinomina qui: rc {rc}, {d}"
    if (t.get("titolo"), t.get("fonte"), t.get("portato")) != ("Nome mio della sessione", "persona", False):
        return f"rinomina non scrive il titolo con fonte persona: {t}"
    rc, d, _ = lancia("rinomina", "qui", sid, "--portato", "--", "Un altro nome")
    if rc != 0 or leggi(titolo).get("portato") is not False:
        return f"--portato con un nome che non è più quello segna lo stesso: {d}, {leggi(titolo)}"
    rc, d, _ = lancia("rinomina", "qui", sid, "--portato", "--", "Nome mio della sessione")
    t = leggi(titolo)
    if rc != 0 or t.get("portato") is not True or t.get("titolo") != "Nome mio della sessione" or t.get("fonte") != "persona":
        return f"--portato non segna il nome come portato: {d}, {t}"
    rc, d, _ = lancia("progetto", "qui", sid, "--", "due-mondi")
    p = leggi(scheda) if scheda.exists() else {}
    if rc != 0 or d != {"ok": True, "progetto": "due-mondi", "iniziato": False} or (p.get("progetto"), p.get("fonte"), p.get("inizio")) != ("due-mondi", "persona", False):
        return f"progetto qui: rc {rc}, {d}, file {p}"
    # /inizio del progetto nuovo (#5465): --iniziato chiude il segno solo sul progetto di adesso
    rc, d, _ = lancia("progetto", "qui", sid, "--iniziato", "--", "altro")
    if rc != 0 or d.get("iniziato") is not False or leggi(scheda).get("inizio") is not False or leggi(scheda).get("progetto") != "due-mondi":
        return f"--iniziato su un progetto che non è più quello lo segna lo stesso, o cambia il progetto: {d}, {leggi(scheda)}"
    rc, d, _ = lancia("progetto", "qui", sid, "--iniziato", "--", "due-mondi")
    if rc != 0 or d.get("iniziato") is not True or leggi(scheda).get("inizio") is not True:
        return f"--iniziato non segna la sessione ripartita da /inizio: {d}, {leggi(scheda)}"
    rc, d, _ = lancia("progetto", "qui", sid, "--", "due-mondi")
    if d.get("iniziato") is not True or leggi(scheda).get("inizio") is not True:
        return f"lo stesso progetto di nuovo chiede un altro /inizio: {d}, {leggi(scheda)}"
    scheda.write_text(json.dumps({"stato": "lavoro", "progetto": "vecchio", "fonte": "inizio", "quando": 1}), encoding="utf-8")
    lancia("progetto", "qui", sid, "--", "due-mondi")
    p = leggi(scheda)
    if (p.get("stato"), p.get("progetto"), p.get("fonte"), p.get("inizio")) != ("lavoro", "due-mondi", "persona", False):
        return f"progetto non tiene lo stato della scheda che c'era, o non chiede /inizio del progetto nuovo: {p}"
    for strano in (["inizia", "qui", "--all", sid, "x"], ["inizia", "qui", "aaaa1111", sid, "Due Mondi"], ["inizia", "qui", "aaaa1111", sid]):
        rc, d, ch = lancia(*strano)
        if rc == 0 or ch:
            return f"{strano} non rifiutato, o lanciato lo stesso: rc {rc}, {d}"
    for strano in (["progetto", "qui", sid, "--", "Due Mondi"], ["progetto", "qui", sid], ["progetto", "qui", "--all", "--", "x"],
                   ["rinomina", "qui", "abc;rm", "--", "x"], ["rinomina", "qui"], ["progetto", "Torre", sid, "--", "../x"]):
        rc, d, ch = lancia(*strano)
        if rc == 0 or ch:
            return f"{strano} non rifiutato, o lanciato lo stesso: rc {rc}, {d}"
    rc, d, ch = lancia("rinomina", "Torre", sid, "--", "Nome mio")
    fuori = [c for c in ch if c[:2] == ["exec", "--on"]]
    arg = json.loads(base64.b64decode(fuori[-1][-1]).decode("utf-8")) if fuori else None
    if rc != 0 or d.get("titolo") != "Nome mio" or not fuori or fuori[-1][2:4] != ["Torre", "python3"]:
        return f"rinomina su Torre non passa da hc exec: rc {rc}, {d}, {[c[:4] for c in ch]}"
    if arg != {"cosa": "titolo", "sessionId": sid, "valore": "Nome mio", "portato": False}:
        return f"rinomina su Torre: alla macchina arriva {arg}"
    rc, d, ch = lancia("progetto", "Torre", sid, "--", "due-mondi")
    fuori = [c for c in ch if c[:2] == ["exec", "--on"]]
    arg = json.loads(base64.b64decode(fuori[-1][-1]).decode("utf-8")) if fuori else None
    if rc != 0 or arg != {"cosa": "scheda", "sessionId": sid, "valore": "due-mondi", "iniziato": False}:
        return f"progetto su Torre: rc {rc}, alla macchina arriva {arg}"
    # hooks/scheda-terminale.py: il progetto della persona resta
    hs = repo / "hooks/scheda-terminale.py"
    base = casa / "progetti"
    (base / "altro").mkdir(parents=True)

    def evs(nome: str, sessione: str = sid, **dati) -> int:
        d_ = {"hook_event_name": nome, "session_id": sessione, "cwd": str(base / "altro"), **dati}
        return subprocess.run([sys.executable, str(hs)], input=json.dumps(d_), capture_output=True, text=True, timeout=60,
                              env={**env, "PROJECTS_BASE": str(base)}).returncode

    scheda.write_text(json.dumps({"stato": "nuova", "progetto": "due-mondi", "fonte": "persona", "quando": 1}), encoding="utf-8")
    evs("UserPromptSubmit", prompt="/inizio altro -- fare una cosa")
    evs("PostToolUse", tool_name="Write", tool_input={"file_path": str(base / "altro" / "x.md")})
    p = leggi(scheda)
    if (p.get("progetto"), p.get("fonte"), p.get("stato")) != ("due-mondi", "persona", "lavoro"):
        return f"scheda-terminale.py riscrive il progetto scelto dalla persona: {p}"
    if "LAVORANDO · due-mondi" not in uscita.read_text(encoding="utf-8"):
        return "la scheda del terminale non porta il progetto scelto dalla persona"
    evs("SessionEnd")
    if not scheda.exists() or leggi(scheda).get("progetto") != "due-mondi":
        return "SessionEnd toglie il progetto scelto dalla persona: la sessione fermata lo perde nell'elenco"
    altra = radice / "cache" / "scheda" / "altra.json"
    evs("UserPromptSubmit", sessione="altra", prompt="/inizio altro -- fare una cosa")
    if not altra.exists():
        return "scheda-terminale.py non scrive la scheda di una sessione normale"
    evs("SessionEnd", sessione="altra")
    if altra.exists():
        return "SessionEnd non toglie più la scheda di una sessione senza progetto della persona"
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    # hooks/titolo-sessione.py: il nome della persona resta
    ht = repo / "hooks/titolo-sessione.py"
    bindir = casa / "bin"
    bindir.mkdir()
    cl = bindir / "claude"
    cl.write_text(CLAUDE_FINTO_TITOLO, encoding="utf-8")
    os.chmod(cl, 0o755)
    envt = {**env, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", "ARTURO_TITOLI_OGNI": "0"}
    tr = casa / "tr.jsonl"
    tr.write_text(json.dumps({"type": "summary"}) + "\n" + json.dumps({"type": "user", "message": {"content": "Rifai le slide del capitolo due"}}) + "\n"
                  + json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Fatto."}]}}) + "\n", encoding="utf-8")

    def evt(nome: str, sessione: str = sid, prompt: str = "") -> int:
        d_ = {"hook_event_name": nome, "session_id": sessione, "transcript_path": str(tr), "prompt": prompt}
        return subprocess.run([sys.executable, str(ht)], input=json.dumps(d_), capture_output=True, text=True, timeout=60, env=envt).returncode

    chiamate = lambda: [x for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]  # noqa: E731
    evt("UserPromptSubmit", prompt="una richiesta lunga abbastanza per un titolo")
    evt("Stop")
    t = leggi(titolo)
    # il modello può essere chiamato per la sintesi (cosa succede adesso, 12/11/2026), il nome resta
    if (t.get("titolo"), t.get("fonte"), t.get("portato")) != ("Nome mio della sessione", "persona", True):
        return f"titolo-sessione.py riscrive il nome della persona: {t}, {len(chiamate())} chiamate"
    # la pulizia: un nome della persona vecchio resta se la sessione ha una trascrizione, altrimenti va via
    (radice / "projects" / "p").mkdir(parents=True)
    (radice / "projects" / "p" / f"{sid}.jsonl").write_text("{}\n", encoding="utf-8")
    persa = radice / "cache" / "titolo" / "persa.json"
    persa.write_text(json.dumps({"titolo": "Nome di una sessione sparita", "fonte": "persona"}), encoding="utf-8")
    automatico = radice / "cache" / "titolo" / "automatico.json"
    automatico.write_text(json.dumps({"titolo": "Titolo vecchio", "fonte": "modello"}), encoding="utf-8")
    vecchio = time.time() - 30 * 86400
    for f in (titolo, persa, automatico):
        os.utime(f, (vecchio, vecchio))
    evt("Stop", sessione="spazzina")
    if not chiamate():
        return "il fine turno di una sessione senza nome non chiama più il modello"
    if not (radice / "cache" / "titolo" / "spazzina.json").exists():
        return "la pulizia dei titoli toglie anche un titolo appena scritto"
    if not titolo.exists() or persa.exists() or automatico.exists():
        return f"pulizia dei titoli: nome della persona {titolo.exists()}, di una sessione sparita {persa.exists()}, automatico {automatico.exists()}"
    # senza nome il file va via e il titolo torna al modello
    rc, d, _ = lancia("rinomina", "qui", sid)
    if rc != 0 or titolo.exists():
        return f"rinomina senza nome non toglie il nome scritto: rc {rc}, {d}"
    prima = len(chiamate())
    evt("Stop")
    if len(chiamate()) != prima + 1 or leggi(titolo).get("fonte") != "modello":
        return "tolto il nome della persona, il titolo non torna al modello"
    lancia("rinomina", "qui", sid)
    if not titolo.exists():
        return "rinomina senza nome toglie anche un titolo automatico"
    # la sonda porta daPortare nell'elenco finché Claude Code non ha il nome
    cl.write_text(CLAUDE_FINTO_ELENCO, encoding="utf-8")
    hcf = casa / "hc_vuoto.py"
    hcf.write_text('print(\'{"machines": []}\')\n', encoding="utf-8")

    def elenco() -> dict:
        r = subprocess.run([sys.executable, str(sonda), "volta"], capture_output=True, text=True, timeout=60,
                           env={**envt, "VOLTA_HC": json.dumps([sys.executable, str(hcf)])})
        return {x["sessionId"]: x for x in json.loads(r.stdout)["sessioni"]}

    try:
        lancia("rinomina", "qui", "inter-x", "--", "Slide del capitolo due")
        riga = elenco().get("inter-x", {})
        if riga.get("titolo") != "Slide del capitolo due" or riga.get("daPortare") != "Slide del capitolo due":
            return f"la sonda non dice che il nome va portato in Claude Code: {riga.get('titolo')}, {riga.get('daPortare')}"
        lancia("rinomina", "qui", "inter-x", "--portato", "--", "Slide del capitolo due")
        riga = elenco().get("inter-x", {})
        if riga.get("titolo") != "Slide del capitolo due" or riga.get("daPortare") is not None:
            return f"portato il nome, la sonda lo dà ancora da portare: {riga.get('daPortare')}"
        (radice / "cache" / "titolo" / "fatta-x.json").write_text(json.dumps({"titolo": "Titolo del modello", "fonte": "modello"}), encoding="utf-8")
        if elenco().get("fatta-x", {}).get("daPortare") is not None:
            return "la sonda dà da portare un titolo automatico"
        # la sessione spostata dalla persona riparte da /inizio (#5465): daIniziare finché --iniziato
        lancia("progetto", "qui", "inter-x", "--", "due-mondi")
        if elenco().get("inter-x", {}).get("daIniziare") != "due-mondi":
            return f"la sonda non dice che la sessione spostata deve ripartire da /inizio: {elenco().get('inter-x', {}).get('daIniziare')}"
        lancia("progetto", "qui", "inter-x", "--iniziato", "--", "due-mondi")
        if elenco().get("inter-x", {}).get("daIniziare") is not None:
            return "ripartita da /inizio, la sonda la dà ancora da iniziare"
        (radice / "cache" / "scheda" / "fatta-x.json").write_text(json.dumps({"progetto": "vecchio", "fonte": "persona"}), encoding="utf-8")
        if elenco().get("fatta-x", {}).get("daIniziare") is not None:
            return "una sessione spostata prima del segno inizio chiede /inizio a sorpresa"
    except (ValueError, KeyError) as e:
        return f"volta_sonda.py volta: uscita senza elenco ({e})"
    return None


PROVA_CAMBIO_PURO = """
import * as m from %s;
const s = { id: "ab12-cd34", sessionId: "ab12-cd34-x", host: "torre-due" };
const giro = (cosa, v) => m.leggiCambio(m.comandoCambio(s, cosa, v).slice(7));
const b = "\\u2500".repeat(30);
console.log(JSON.stringify({
  comando: m.comandoCambio(s, "nome", "Aè"),
  nome: giro("nome", "  Preventivo  per\\tl'estate \\u00e8 \\ud83d\\ude42  "), lungo: giro("nome", "x".repeat(90)).valore.length, vuoto: giro("nome", "   "),
  progetto: giro("progetto", "Due Mondi"), accenti: giro("progetto", "Caffè & Tè").valore, niente: giro("progetto", " -- "),
  storti: [m.leggiCambio("volta-cambia-altro-0041-ab12"), m.leggiCambio("volta-cambia-nome-004-ab12"), m.leggiCambio("volta-gesto-rinomina-ab12")],
  cambia: m.CAMBIA,
  noti: m.progettiNoti({ sessioni: [{ progetto: "zeta" }, { progetto: null }, { progetto: "Due Mondi" }] }, ["arturo", "zeta", ""]),
  filtro: [m.filtraProgetti(["arturo", "due-mondi", "mondo"], "Mon"), m.filtraProgetti(["a", "b", "c"], "", 2)],
  casella: [m.casellaVuota(`ciao\\n${b}\\n\\u276f \\n${b}\\n  stato`), m.casellaVuota(`${b}\\n\\u276f Try "scrivi qui"\\n${b}`), m.casellaVuota(`${b}\\n> \\n${b}`),
            m.casellaVuota(`${b}\\n\\u276f una bozza\\n${b}`), m.casellaVuota(`${b}\\n\\u276f riga uno\\nriga due\\n${b}`), m.casellaVuota("zsh %% "), m.casellaVuota(""), m.casellaVuota(`${b}\nx\n${b}`)],
  portare: [m.daPortare({ stato: "ferma", daPortare: " Nome " }), m.daPortare({ stato: "lavora", daPortare: "Nome" }), m.daPortare({ stato: "aspetta", daPortare: "Nome" }),
            m.daPortare({ stato: "ferma", daPortare: "Nome", vecchia: true }), m.daPortare({ stato: "ferma", daPortare: null })],
  iniziare: [m.daIniziare({ stato: "ferma", daIniziare: "due-mondi" }), m.daIniziare({ stato: "lavora", daIniziare: "due-mondi" }),
             m.daIniziare({ stato: "aspetta", daIniziare: "due-mondi" }), m.daIniziare({ stato: "ferma", daIniziare: "Due Mondi; rm" }),
             m.daIniziare({ stato: "ferma", daIniziare: "due-mondi", vecchia: true }), m.daIniziare({ stato: "ferma" })],
  // #5506: un nome alternativo (la cartella volta-celeste) e la chiave (herdr-arturo) sono una riga sola
  alias: (() => {
    const v = { chiave: "herdr-arturo", titolo: "Volta" };
    m.impostaProgetti({ "herdr-arturo": v, "volta-celeste": v, volta: v });
    const l = m.progettiNoti({ sessioni: [{ progetto: "volta-celeste" }, { progetto: "Volta" }, { progetto: "zeta" }] }, ["herdr-arturo", "arturo"]);
    m.impostaProgetti({});
    return l;
  })(),
}));
"""

PROVA_CAMBIO = r"""
import { cambiaSessione, rinominaSchede, portaNome, portaInizio, spostaScheda } from "./dati.mjs";
import { lanciati, eseguiti, avvisi, inviati } from "./herdr.mjs";
const caso = process.env.HZ_CASO;
const s = { id: "ffff1111", sessionId: "ffff1111-aaaa", host: "Torre", macchina: "Torre", nome: "Progetto x", titolo: "Rifare il deck",
            progetto: "progetto-x", cartella: "/lavori/x", stato: "ferma", tipo: "background", daPortare: "Nome mio", daIniziare: "due-mondi",
            attach: ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"] };
let esito = null;
if (caso === "nome") esito = await cambiaSessione(s, "nome", "Nome mio");
else if (caso === "togli") esito = await cambiaSessione(s, "nome", "");
else if (caso === "progetto") esito = await cambiaSessione(s, "progetto", "due-mondi");
else if (caso === "schede") esito = rinominaSchede(s, "N".repeat(50));
else if (caso === "porta") esito = await portaNome(s);
else if (caso === "porta-lavora") esito = await portaNome({ ...s, stato: "lavora" });
else if (caso === "inizia") esito = await portaInizio(s);
else if (caso === "inizia-lavora") esito = await portaInizio({ ...s, stato: "lavora" });
else if (caso === "inizia-altrove") esito = await portaInizio(s, false);
else if (caso === "inizia-terminale") esito = await portaInizio({ ...s, tipo: "interattiva", attach: null });
else if (caso === "sposta") esito = await spostaScheda(s, "due-mondi");
else if (caso === "sposta-interattiva") esito = await spostaScheda({ ...s, tipo: "interattiva", attach: null, questa: true, terminale: "t9" }, "due-mondi");
console.log(JSON.stringify({ lanciati, eseguiti, avvisi, inviati, esito }));
"""


def hz59(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    testi = {n: (mod / n).read_text(encoding="utf-8") for n in ("volta.js", "barra.js", "main.js", "menusessione.js", "cambio.js", "dati.js")}
    attesi = (
        ("volta.js", "if (verbo in CAMBIA) return this.chiedi(s, CAMBIA[verbo]);", "Rinomina e Cambia progetto non aprono il dialogo"),
        ("volta.js", 'return e?.click_count >= 2 ? this.chiedi(s, "nome") : this.premi(s, cx);', "il doppio clic sul titolo non apre il dialogo del nome"),
        ("volta.js", "const d = leggiCambio(c);", "il comando del cambio non passa da leggiCambio"),
        ("volta.js", "r = await cambiaSessione(s, cosa, valore);", "il cambio non arriva alla sonda"),
        ("volta.js", 'if (r.ok && cosa === "nome" && valore) rinominaSchede(s, valore);', "il nome nuovo non va sulla scheda"),
        ("volta.js", 'if (r.ok && cosa === "progetto" && String(s.progetto ?? "") !== valore) dopo = await spostaScheda(s, valore);', "il progetto nuovo non sposta la scheda"),
        ("volta.js", "    this.portaNomi();\n", "a ogni lettura i nomi non vanno in Claude Code"),
        ("volta.js", "if (!daPortare(s) || this.porto[k]) continue;", "un nome si porta due volte insieme"),
        ("volta.js", "    this.portaInizi();\n", "a ogni lettura le sessioni spostate non ripartono da /inizio (#5465)"),
        ("volta.js", "if (!daIniziare(s) || this.inizio[k]) continue;", "una sessione spostata riparte due volte insieme"),
        ("volta.js", "portaInizio(s, this.spostate[k] === s.daIniziare)", "la ripresa da /inizio parte da ogni finestra, non solo da quella che ha spostato"),
        ("volta.js", 'if (r.ok && cosa === "progetto" && r.iniziato === false) this.spostate[k] = valore;', "Cambia progetto non segna la sessione da riprendere"),
        ("volta.js", "nomiProgetti().catch(() => []).then((l) => apriCambio(s, cosa, progettiNoti(this.dati, l)));", "il dialogo del progetto non riceve i progetti noti"),
        ("barra.js", 'else if (c === "volta-cambia") this.volta.cambiaComando(arg, cx);', "barra.js non legge il comando del cambio"),
        ("main.js", "cambio: Cambio,", "main.js non monta il dialogo del cambio"),
        ("menusessione.js", "const cambi = this.voci.filter((v) => GRUPPI_MENU[1].includes(v.verbo));", "il menu non mostra Rinomina e Contesto nel secondo gruppo"),
        ("menusessione.js", ".when(cambi.length > 0, (el) => el.child(gruppo(cambi)))", "il menu non disegna il gruppo di Rinomina e Cambia progetto"),
        ("cambio.js", 'openOverlay({ mod: "arturo", props: { parte: "cambio", sessione: s, cosa, noti }, kind: "dialog"', "il cambio non è un dialogo del mod"),
        ("cambio.js", "    run(comandoCambio(this.s, this.cosa, valore));\n    this.chiudi();", "il dialogo si chiude prima di mandare il cambio"),
        ("cambio.js", 'if (this.cosa === "progetto" && !valore) return;', "il dialogo manda un progetto vuoto"),
        ("cambio.js", 'this.input.on("submit", () => this.conferma());', "Invio non conferma"),
        ("cambio.js", 'const valore = this.cosa === "nome" ? titolo(this.s) : String(this.s.progetto ?? "");', "il dialogo non parte dal nome o dal progetto di adesso"),
    )
    for file, pezzo, motivo in attesi:
        if pezzo not in testi[file]:
            return f"{file}: {motivo}"
    # #5504: il titolo del dialogo del progetto ripete la voce del menu, senza i puntini.
    voce = re.search(r'\{ verbo: "progetto", testo: "([^"]+)" \}', (mod / "sessioni.js").read_text(encoding="utf-8"))
    titolo = re.search(r'progetto: \{ titolo: "([^"]+)"', testi["cambio.js"])
    if not voce or not titolo or titolo.group(1) != voce.group(1).rstrip("…"):
        return f"cambio.js: il titolo del dialogo ({titolo and titolo.group(1)!r}) non ripete la voce del menu ({voce and voce.group(1)!r})"
    cj = (mod / "comandi.js").read_text(encoding="utf-8")
    if cj.index('c.startsWith("volta-cambia-")') > cj.index(CLIC_VOLTA):
        return "comandi.js: volta-cambia-… finisce nel clic su una sessione, che viene prima"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "sessioni.mjs"
    shutil.copyfile(mod / "sessioni.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_CAMBIO_PURO % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    # il cambio porta la chiave macchina:id (#5643), anche con una macchina che ha trattini
    puri = {"comando": "arturo.volta-cambia-nome-004100e8-torre-due:ab12-cd34",
            "nome": {"cosa": "nome", "valore": "Preventivo per l'estate è 🙂", "id": "torre-due:ab12-cd34"}, "lungo": 60,
            "vuoto": {"cosa": "nome", "valore": "", "id": "torre-due:ab12-cd34"},
            "progetto": {"cosa": "progetto", "valore": "due-mondi", "id": "torre-due:ab12-cd34"}, "accenti": "caffe-te", "niente": None,
            "storti": [None, None, None], "cambia": {"rinomina": "nome", "progetto": "progetto"},
            "noti": ["arturo", "due-mondi", "zeta"], "filtro": [["mondo", "due-mondi"], ["a", "b"]],
            "casella": [True, True, True, False, False, False, False, False], "portare": ["Nome", None, None, None, None],
            "iniziare": ["due-mondi", None, None, None, None, None], "alias": ["arturo", "herdr-arturo", "zeta"]}
    for k, v in puri.items():
        if d.get(k) != v:
            return f"sessioni.js, {k}: {d.get(k)}, atteso {v}"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, testi["dati.js"])
    (m / "prova.mjs").write_text(PROVA_CAMBIO, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base", "volta": "/v/volta_sonda.py"}), encoding="utf-8")
    spazio = {"id": "s1", "name": "progetto-x", "named": True, "active": True, "tabs": [{"id": "tb1"}, {"id": "tb2"}]}
    herdr = {"spaces": [spazio], "panes": [{"terminal": "t7", "tab": "tb1"}, {"terminal": "t8", "tab": "tb2"}, {"terminal": "t9", "tab": "tb2"}],
             "terminals": [{"address": "t7", "argv": ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]}, {"address": "t9", "argv": ["zsh"]},
                           {"address": "t8", "argv": ["zsh"], "labels": {"arturo.sessione": "ffff1111"}}]}
    bordo = "─" * 30
    vuota = f"ciao\n{bordo}\n❯ \n{bordo}\n  stato"
    bozza = f"{bordo}\n❯ una bozza non inviata\n{bordo}"
    nuda = {"state": "live", "pid": 5, "argv": ["zsh", "-c", "claude attach ffff1111"], "foreground": {"pid": 5, "argv": ["zsh"]}}

    def volta(caso, schermo=vuota, **extra):
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso, "HZ_EXEC": json.dumps({"ok": True}),
             "HZ_HERDR": json.dumps(extra.pop("herdr", herdr)), "HZ_HC_READ": json.dumps({"t7": schermo}), "HZ_CHIUDE": "1", **extra}
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    sonda = lambda v: [x[2:] for x in v["eseguiti"] if x[1:2] == ["/v/volta_sonda.py"]]  # noqa: E731
    try:
        v = volta("nome")
        if sonda(v) != [["rinomina", "Torre", "ffff1111-aaaa", "--", "Nome mio"]] or v["esito"] != {"ok": True}:
            return f"Rinomina non chiama la sonda sulla macchina della sessione, col sessionId: {sonda(v)}, {v['esito']}"
        v = volta("togli")
        if sonda(v) != [["rinomina", "Torre", "ffff1111-aaaa"]]:
            return f"un nome vuoto non toglie il nome scritto: {sonda(v)}"
        v = volta("progetto")
        if sonda(v) != [["progetto", "Torre", "ffff1111-aaaa", "--", "due-mondi"]]:
            return f"Cambia progetto non chiama la sonda: {sonda(v)}"
        v = volta("schede")
        if v["esito"] != 1 or v["lanciati"] != [{"cmd": "tab.rename", "id": "tb1", "name": "N" * 40}]:
            return f"il nome nuovo non va sulla sola scheda che è tutta della sessione: {v['esito']}, {v['lanciati']}"
        v = volta("porta")
        if v["esito"] is not True or ["send", "t7", "/rename Nome mio"] not in v["inviati"]:
            return f"a sessione ferma e casella vuota il nome non va in Claude Code con /rename: {v['esito']}, {v['inviati']}"
        if sonda(v) != [["rinomina", "Torre", "ffff1111-aaaa", "--portato", "--", "Nome mio"]]:
            return f"portato il nome, la sonda non lo segna: {sonda(v)}"
        for motivo, extra in (("con una bozza nella casella", {"schermo": bozza}), ("mentre la sessione lavora", {"caso": "porta-lavora"}),
                              ("in una scheda rimasta con la shell", {"HZ_HC_GET": json.dumps({"t7": [nuda]})}),
                              ("senza una scheda in questa finestra", {"herdr": {"spaces": [spazio]}})):
            v = volta(extra.pop("caso", "porta"), **extra)
            if v["esito"] is not False or any(x[0] == "send" for x in v["inviati"]) or sonda(v):
                return f"/rename scritto {motivo}: {v['esito']}, {v['inviati']}, {sonda(v)}"
        v = volta("porta", HZ_HC_READ=json.dumps({"t7": vuota, "t8": vuota}))
        if v["esito"] is not True or len([x for x in v["inviati"] if x[0] == "send"]) != 1:
            return f"con due schede buone /rename va scritto una volta sola: {v['inviati']}"
        v = volta("porta", HZ_HC_ROTTO="send")
        if v["esito"] is not False or sonda(v):
            return f"/rename non scritto, ma il nome risulta portato: {v['esito']}, {sonda(v)}"
        # la sessione spostata riparte da /inizio del progetto nuovo (#5465)
        segnata = ["progetto", "Torre", "ffff1111-aaaa", "--iniziato", "--", "due-mondi"]
        v = volta("inizia")
        if v["esito"] != {"fatto": True, "come": "scheda"} or ["send", "t7", "/inizio due-mondi"] not in v["inviati"] or sonda(v) != [segnata]:
            return f"a sessione ferma con la scheda aperta /inizio non va nella scheda, o non si segna: {v['esito']}, {v['inviati']}, {sonda(v)}"
        for motivo, extra in (("mentre la sessione lavora", {"caso": "inizia-lavora"}), ("con una bozza nella casella", {"schermo": bozza}),
                              ("senza scheda, da una finestra che non l'ha spostata", {"caso": "inizia-altrove", "herdr": {"spaces": [spazio]}})):
            v = volta(extra.pop("caso", "inizia"), **extra)
            if v["esito"] != {"fatto": False} or any(x[0] == "send" for x in v["inviati"]) or sonda(v):
                return f"/inizio scritto o ripresa partita {motivo}: {v['esito']}, {v['inviati']}, {sonda(v)}"
        v = volta("inizia", herdr={"spaces": [spazio]})
        if v["esito"] != {"fatto": True, "come": "ripresa"} or sonda(v) != [["inizia", "Torre", "ffff1111", "ffff1111-aaaa", "due-mondi", "--cartella", "/lavori/x"], segnata]:
            return f"senza scheda la sessione in background non riparte da /inizio con la sonda: {v['esito']}, {sonda(v)}"
        v = volta("inizia-terminale", herdr={"spaces": [spazio]})
        if v["esito"] != {"fatto": True, "come": "terminale"} or sonda(v) != [segnata]:
            return f"un'interattiva in un Terminale: {v['esito']}, {sonda(v)}"
        v = volta("sposta", HZ_NASCE="t20")
        chiuse = [x for x in v["lanciati"] if x["cmd"] in ("tab.close", "terminal.kill")]
        nuove = [x for x in v["lanciati"] if x["cmd"] in ("tab.new", "space.new")]
        if sorted(json.dumps(x, sort_keys=True) for x in chiuse) != sorted(json.dumps(x, sort_keys=True) for x in ({"cmd": "tab.close", "id": "tb1", "confirmed": True}, {"cmd": "terminal.kill", "terminal": "t8"})):
            return f"cambiato il progetto, gli agganci di prima non si chiudono: {chiuse}"
        if v["esito"] != {"spostata": True} or len(nuove) != 1 or nuove[0]["cmd"] != "space.new" or nuove[0].get("name") != "due-mondi" or nuove[0].get("argv") != ["ssh", "-t", *OPZIONI_SSH, "torre.lan", "claude", "attach", "ffff1111"]:
            return f"la sessione non si riapre nello spazio del progetto nuovo: {v['esito']}, {nuove}"
        v = volta("sposta-interattiva")
        if v["esito"] != {"resta": True} or v["lanciati"]:
            return f"un'interattiva che gira in una scheda viene chiusa o spostata: {v['esito']}, {v['lanciati']}"
        v = volta("sposta", herdr={"spaces": [spazio]})
        if v["esito"] != {} or v["lanciati"]:
            return f"una sessione senza scheda aperta ne apre una al cambio di progetto: {v['esito']}, {v['lanciati']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    return None



PROVA_MEMORIA = r"""
import { progetti, sezioni, progettiMemoria, nomiProgetti, FERME } from "./dati.mjs";
import { eseguiti } from "./herdr.mjs";
const vista = { oggi: "2026-11-11", gruppi: [{ tipo: "tu", todo: [{ progetto: "ariaperta" }] }],
  progetti: [{ nome: "ariaperta", slug: "ariaperta", titolo: "Tutto Vero", categoria: "Prodotti", riga: "riga dei todo", parola: "va" }] };
const voce = (slug, piu = {}) => ({ slug, nome: slug, titolo: "", categoria: "", riga: "", data: "", cartella: false, handoff: false, alias: [], ...piu });
const memoria = [
  voce("tuttovero", { titolo: "Tutto Vero", categoria: "Prodotti", riga: "passo", data: "2026-11-10", cartella: true, handoff: true, alias: ["ariaperta"] }),
  voce("solo-handoff", { riga: "PROSSIMO PASSO", data: "2026-11-09", handoff: true }),
  voce("vecchio", { riga: "passo vecchio", data: "2026-09-01", handoff: true }),
  voce("cartella-nuda", { nome: "Cartella Nuda", cartella: true }),
];
const lista = progetti(vista, { memoria, cartelle: ["non-deve-entrare"] });
const tante = Array.from({ length: 150 }, (_, i) => voce(`p-${i}`, { riga: "x", data: "2026-11-01", handoff: true, cartella: true }));
sezioni(progetti(vista, { memoria: tante }));
const t0 = performance.now();
for (let i = 0; i < 5; i++) sezioni(progetti(vista, { memoria: tante }));
const ms = (performance.now() - t0) / 5;
const m = await progettiMemoria();
console.log(JSON.stringify({
  chiavi: lista.map((p) => p.chiave),
  tv: lista.find((p) => p.chiave === "tuttovero"),
  sh: lista.find((p) => p.chiave === "solo-handoff"),
  sezioni: sezioni(lista).map((s) => [s.titolo, s.progetti.map((p) => p.chiave), Boolean(s.chiusa)]),
  ferme: FERME, ms,
  prima: progetti(vista, { cartelle: ["solo-cartella"], stati: { "solo-cartella": { riga: "R" } } }).map((p) => [p.chiave, p.categoria, p.riga]),
  memoria: m, nomi: await nomiProgetti(), argv: eseguiti.map((a) => a.slice(-2)),
}));
"""


def hz61(repo: Path, casa: Path) -> str | None:
    mod_dir = repo / "shared/volta/mods/arturo"
    barra = (mod_dir / "barra.js").read_text(encoding="utf-8")
    for pezzo in ("this.memoria = await progettiMemoria();", "if (!this.memoria) {", "memoria: this.memoria ?? null",
                  "for (const a of p.alias ?? []) if (!(a in mappa)) mappa[a] = mappa[p.chiave];"):
        if pezzo not in barra:
            return f"barra.js non ha più: {pezzo}"
    if "const [lista, sessioni] = await Promise.all([nomiProgetti(), sessioniVolta()]);" not in (mod_dir / "apri.js").read_text(encoding="utf-8"):
        return "Cerca non legge nomiProgetti"
    if "nomiProgetti().catch(() => []).then((l) => apriCambio(" not in (mod_dir / "volta.js").read_text(encoding="utf-8"):
        return "Cambia progetto non legge nomiProgetti"
    node = shutil.which("node")
    if not node:
        return None
    mod = casa / "mod"
    mod.mkdir()
    mod_dati(repo, mod, (mod_dir / "dati.js").read_text(encoding="utf-8"))
    (mod / "prova.mjs").write_text(PROVA_MEMORIA, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python3", str(casa / "bin" / "arturo")], "radice": str(repo),
                                                 "base": str(casa)}), encoding="utf-8")
    risposta = json.dumps({"versione": 1, "progetti": [{"slug": "a", "nome": "A Maiuscola", "cartella": True},
                                                       {"slug": "b", "nome": "b", "cartella": False}]})
    esiti = {}
    for nome, piu in (("con", {"HZ_EXEC": risposta}), ("senza", {})):
        env = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), **piu}
        env.pop("HZ_EXEC", None) if not piu else None
        r = subprocess.run([node, str(mod / "prova.mjs")], capture_output=True, text=True, timeout=30, env=env)
        if r.returncode != 0:
            return f"dati.js non gira ({nome}): {(r.stderr or r.stdout).strip()[:200]}"
        esiti[nome] = json.loads(r.stdout.strip().splitlines()[-1])
    e = esiti["con"]
    if e["chiavi"].count("tuttovero") != 1 or "ariaperta" in e["chiavi"] or "non-deve-entrare" in e["chiavi"]:
        return f"alias o cartelle doppie: {e['chiavi']}"
    tv, sh = e["tv"], e["sh"]
    if tv["tu"] != 1 or tv["nome"] != "ariaperta" or tv["alias"] != ["ariaperta"] or tv["riga"] != "riga dei todo":
        return f"la riga del progetto con alias non tiene conti, nome della fonte e alias: {tv}"
    if not sh or sh["riga"] != "PROSSIMO PASSO" or sh["calcolato"] or sh["nome"] != "solo-handoff":
        return f"il progetto che vive solo negli handoff non ha la sua riga: {sh}"
    attese = [["Prodotti", ["tuttovero"], False], ["Progetti", ["solo-handoff"], False],
              ["Altre cartelle", ["cartella-nuda"], False], [e["ferme"], ["vecchio"], True]]
    if e["sezioni"] != attese:
        return f"sezioni: {e['sezioni']}"
    if e["ms"] > 50:
        return f"150 voci: {e['ms']:.1f} ms a giro, oltre i 50 del render"
    if ["solo-cartella", "Altre cartelle", "R"] not in e["prima"]:
        return f"senza memoria l'elenco non è quello di prima: {e['prima']}"
    if e["nomi"] != ["A Maiuscola", "b"] or ["progetti", "--json"] not in e["argv"]:
        return f"nomiProgetti con la memoria: {e['nomi']} {e['argv']}"
    s = esiti["senza"]
    if s["memoria"] is not None or s["nomi"] != []:
        return f"con un Arturo senza il comando: memoria={s['memoria']} nomi={s['nomi']}"
def hz60(repo: Path, casa: Path) -> str | None:
    import base64  # noqa: PLC0415
    import importlib.util  # noqa: PLC0415
    import zlib  # noqa: PLC0415
    sp = importlib.util.spec_from_file_location("volta_sonda_hz60", repo / "shared/volta/mods/arturo/volta_sonda.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    spazio: dict = {}
    exec(getattr(m, "TERMINALE", ""), spazio)  # noqa: S102
    terminale_di = spazio.get("terminale_di")
    if not callable(terminale_di):
        return "volta_sonda.py non ha terminale_di() nel blocco TERMINALE"
    dorme = [sys.executable, "-c", "import time; time.sleep(30)"]
    senza = {k: v for k, v in os.environ.items() if k != "HC_TERMINAL_ID"}
    dentro = subprocess.Popen(dorme, env={**senza, "HC_TERMINAL_ID": "t9z"})
    fuori = subprocess.Popen(dorme, env=senza)
    try:
        letto = None
        for _ in range(20):  # su Windows l'ambiente si legge appena il processo ha finito di nascere
            letto = terminale_di(dentro.pid)
            if letto:
                break
            time.sleep(0.25)
        if letto != "t9z":
            return f"terminale_di non legge HC_TERMINAL_ID di un processo vero: {letto!r}"
        if terminale_di(fuori.pid) is not None:
            return "terminale_di dà un terminale a un processo nato fuori da Herdr"
    finally:
        dentro.kill()
        fuori.kill()
    if terminale_di(4000000) is not None:
        return "terminale_di dà un terminale a un processo che non esiste"
    if "#TERMINALE#" in m.SONDA or "def terminale_di(pid):" not in m.SONDA:
        return "la SONDA non porta dentro terminale_di"
    if 'if s.get("kind") != "background" and isinstance(s.get("pid"), int):\n        s["terminale"] = terminale_di(s["pid"])' not in m.SONDA:
        return "la SONDA non chiede il terminale delle sole interattive"
    try:
        compile(m.SONDA, "SONDA", "exec")
    except SyntaxError as e:
        return f"la SONDA non è Python valido: {e}"
    righe: list = []
    m.hc = lambda: ["hc"]
    m.lancia = lambda argv, timeout=60: (righe.append(argv), (0, '{"claude": null, "sessioni": []}', ""))[1]
    m.sonda_remota("amaltea")
    codice = righe[0][-1] if righe else ""
    if len(codice) >= 8000:
        return f"la sonda verso un'altra macchina è una riga di {len(codice)} caratteri: cmd.exe ne regge 8191"
    try:
        dentro_riga = codice.split("'")[1]
        if zlib.decompress(base64.b64decode(dentro_riga)).decode("utf-8") != m.senza_commenti(m.SONDA):
            return "la riga compressa non torna la SONDA (senza le righe di commento)"
        spazio = {"exec": lambda testo: righe.append(testo)}
        exec(codice, spazio)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        return f"la riga della sonda remota non si apre: {type(e).__name__}: {e}"
    if righe[-1] != m.senza_commenti(m.SONDA).encode("utf-8"):
        return "la riga della sonda remota non esegue la SONDA"
    return None


PROVA_ELEMENTO = r"""
const { evidenza, elementoSotto, nomeElemento, nota } = await import(%s);
const mis = (l, a) => ({ larghezza: l, altezza: a });
const m = { finestra: mis(1440, 900), marchio: mis(292, 54), barra: mis(292, 690), piede: mis(292, 156),
  testata: mis(1147, 54), stato: mis(1147, 30), todo: mis(340, 792), divisore: 1, padding: 12, gap: 12 };
const e = (id, x, y, width, height, view, order, own = false) => ({ id, x, y, width, height, view, own, order });
const el = [e("misura-barra", 0, 54, 292, 690, 1, 1), e("volta-elenco", 0, 200, 292, 200, 1, 2),
  e("vr-amaltea-ab12", 8, 210, 276, 44, 1, 3), e("va-amaltea-ab12", 250, 220, 24, 24, 1, 4),
  e("misura-testata", 293, 0, 1147, 54, 2, 5), e("chiedi", 1000, 12, 160, 30, 2, 6),
  e("misura-piede", 0, 744, 292, 156, 3, 7), e("chiedi", 8, 752, 276, 32, 3, 8),
  e("nota-velo", 0, 0, 1440, 900, 9, 9, true), e("nota-segno-x", 100, 215, 22, 22, 9, 10),
  e("piccolo-del-velo", 98, 218, 4, 4, 9, 11, true), e("vuoto", 100, 215, 0, 10, 1, 12),
  e("altro-mod", 700, 400, 50, 50, 7, 13)];
const s = (x, y) => elementoSotto({ x, y }, el);
console.log(JSON.stringify({
  nomi: ["vr-x", "v-x", "vg-x-stop", "t-12", "todo-aggiungi", "todo-elenco-p", "dafare", "scheda-3", "boh"].map(nomeElemento),
  riga: s(100, 220), azioni: s(260, 230)?.id, testata: s(1010, 20)?.nome, piede: s(20, 760)?.nome,
  parte: s(100, 600), straniero: s(710, 410), niente: s(700, 300), senza: elementoSotto({ x: 100, y: 220 }, null),
  ev: evidenza({ x: 100, y: 220 }, m, el), prima: evidenza({ x: 600, y: 400 }, m),
  misto: evidenza({ x: 600, y: 400 }, m, el)?.nome, alto: evidenza({ x: 1010, y: 20 }, m, el)?.etichetta,
  bordo: evidenza({ x: 1420, y: 20 }, m, [e("misura-testata", 293, 0, 1147, 54, 2, 1), e("dafare", 1300, 12, 136, 30, 2, 2)])?.etichetta,
  marchio: evidenza({ x: 100, y: 20 }, m)?.etichetta, barra: evidenza({ x: 100, y: 300 }, { ...m, marchio: mis(292, 0), barra: mis(292, 744) })?.etichetta,
  senzaMisure: evidenza({ x: 100, y: 220 }, { finestra: mis(1440, 900) }, el)?.nome,
  nulla: evidenza({ x: 100, y: 220 }, { finestra: mis(1440, 900) }),
  todo: nota({ testo: "x", x: 1, y: 2, larghezza: 3, altezza: 4, progetto: "p", cartella: "/c", quando: "q",
    dove: { blocco: "progetti", elemento: { id: "vr-a", nome: "Riga di sessione · Barra dei progetti" } } }),
}));
"""


def hz62(repo: Path, casa: Path) -> str | None:
    """Il velo delle note sul singolo elemento: le funzioni pure di nota.js, con elementi finti come li dà
    window.elements() di Volta."""
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "nota.mjs"
    shutil.copyfile(repo / "shared/volta/mods/arturo/nota.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_ELEMENTO % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"nota.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    nomi = ["Riga di sessione", "Sessione", "Gesto della sessione", "Cosa da fare", "Aggiungi un todo",
            "Elenco delle cose da fare", "Mostra o nascondi Da fare", "Scheda", None]
    if g["nomi"] != nomi:
        return f"nomeElemento() sbaglia i nomi: {g['nomi']}"
    riga = {"id": "vr-amaltea-ab12", "nome": "Riga di sessione · Barra dei progetti", "blocco": "progetti", "parte": "barra",
            "rettangolo": {"x": 8, "y": 210, "larghezza": 276, "altezza": 44}}
    if g["riga"] != riga:
        return f"elementoSotto() non prende la riga sotto il punto (o prende un pezzo del velo): {g['riga']}"
    if g["azioni"] != "va-amaltea-ab12":
        return f"fra due elementi sotto il punto non vince il più piccolo: {g['azioni']}"
    if g["testata"] != "Cosa posso chiedere · Testata" or g["piede"] != "Cosa posso chiedere · Piede della barra":
        return f"lo stesso id in due parti non si distingue: {g['testata']} / {g['piede']}"
    if (g["parte"] or {}).get("id") != "misura-barra" or g["parte"]["nome"] != "Barra dei progetti":
        return f"fuori da ogni elemento non resta la parte: {g['parte']}"
    if (g["straniero"] or {}).get("nome") != "altro-mod" or g["straniero"]["blocco"] is not None:
        return f"un elemento di un altro mod non porta il suo id come nome: {g['straniero']}"
    if g["niente"] is not None or g["senza"] is not None:
        return "elementoSotto() inventa un elemento dove non ce ne sono"
    ev = g["ev"] or {}
    if ev.get("elemento") != {"id": riga["id"], "nome": riga["nome"], "rettangolo": riga["rettangolo"]} \
            or ev.get("nome") != riga["nome"] or ev.get("rettangolo") != riga["rettangolo"] or ev.get("blocco") != "progetti":
        return f"evidenza() non mette in luce l'elemento: {ev}"
    fasce = [{"x": 0, "y": 0, "larghezza": 1440, "altezza": 210}, {"x": 0, "y": 254, "larghezza": 1440, "altezza": 646},
             {"x": 0, "y": 210, "larghezza": 8, "altezza": 44}, {"x": 284, "y": 210, "larghezza": 1156, "altezza": 44}]
    if ev.get("fasce") != fasce or ev.get("etichetta") != {"x": 8, "y": 186, "dentro": False}:
        return f"fasce o etichetta del riquadro non tornano: {ev.get('fasce')} {ev.get('etichetta')}"
    prima = g["prima"] or {}
    if prima.get("nome") != "Sessione" or prima.get("elemento") is not None or prima.get("blocco") != "main" \
            or prima.get("rettangolo") != {"x": 305, "y": 66, "larghezza": 771, "altezza": 792}:
        return f"senza elementi evidenza() non resta sulla parte: {prima}"
    if g["misto"] != "Sessione":
        return f"sulla sessione, dove non ci sono elementi, evidenza() non ricade sulla parte: {g['misto']}"
    if g["alto"] != {"x": 1000, "y": 44, "dentro": False}:
        return f"l'etichetta di un bottone in cima alla finestra lo copre invece di stargli sotto: {g['alto']}"
    if g["bordo"] != {"x": 1189, "y": 44, "dentro": False}:
        return f"l'etichetta di un elemento sul bordo destro esce dalla finestra: {g['bordo']}"
    if g["marchio"] != {"x": 0, "y": 56, "dentro": False} or g["barra"] != {"x": 0, "y": 4, "dentro": True}:
        return f"l'etichetta di una parte in cima non sta sotto se è bassa e dentro se è alta: {g['marchio']} {g['barra']}"
    if g["senzaMisure"] != riga["nome"] or g["nulla"] is not None:
        return "senza le misure delle parti l'elemento non basta, o evidenza() inventa un riquadro"
    todo = g["todo"]
    if todo["dati"]["dove"].get("elemento", {}).get("id") != "vr-a" \
            or "parte progetti, su Riga di sessione · Barra dei progetti (vr-a)" not in todo["argv"][8]:
        return "nota.json e il todo non portano l'elemento"
    return None


def hz64(repo: Path, casa: Path) -> str | None:
    """Il velo usa gli elementi solo dove la finestra li dà, e le parti hanno gli id che servono."""
    mod = repo / "shared/volta/mods/arturo"
    ui = (mod / "notaui.js").read_text(encoding="utf-8")
    for pezzo, cosa in (
            ('const ELEMENTI = typeof W?.elements === "function" && typeof W?.track_elements === "function";',
             "non controlla che la finestra abbia window.elements (Herdr non ce l'ha)"),
            ("    segui(true);\n", "non accende il registro degli elementi all'apertura"),
            ("  close() { segui(false); }", "non spegne il registro degli elementi alla chiusura"),
            ("elemento: ev?.elemento ?? null,", "non salva l'elemento nel dove della nota"),
            ("if (chiave(sotto(this.sopra, this.dim)) !== this.vista) cx.notify();",
             "non si ridisegna quando cambia l'elemento sotto il puntatore")):
        if pezzo not in ui:
            return f"notaui.js {cosa}"
    for file, ids in (("volta.js", ('`vgh-${g.chiave || "senza"}`',)),
                      ("testata.js", ('"testata-titolo"', '"testata-stato"', '"stato-tasti"', '"stato-lavoro"', '"benvenuto-titolo"')),
                      ("todo.js", ('"todo-titolo"', '"todo-progetto"', "`poi-${i}`"))):
        testo = (mod / file).read_text(encoding="utf-8")
        for i in ids:
            if f".id({i})" not in testo and f"pezzo({i}," not in testo:
                return f"{file} non dà l'id {i} al suo elemento: il velo non lo può mettere in luce"
    return None


PROVA_MICROFONO = """
import { bersaglio, passo, rigaMicrofono, RINNOVO, IN_AVVIO, TENUTA } from %s;
const ssh = (id, altro = {}) => ({ id, questa: false, macchina: "Amaltea", attach: ["ssh", "-t", "amaltea", "/c/claude", "attach", id], ...altro });
const sessioni = [ssh("aaaa1111"), { id: "bbbb2222", questa: true, macchina: "Qui", attach: ["/c/claude", "attach", "bbbb2222"] },
  ssh("cccc3333", { attach: ["ssh", "-t", "amaltea", "top", "-l", "1"] }), ssh("dddd4444", { attach: ["ssh", "-t", "-oProxyCommand=x", "/c/claude", "attach", "dddd4444"] }),
  ssh("eeee5555", { attach: ["C:\\\\Windows\\\\System32\\\\OpenSSH\\\\ssh.exe", "-t", "feder@torre", "claude", "attach", "eeee5555"], macchina: "Torre" }),
  ssh("ffff6666", { attach: ["mosh", "-t", "amaltea", "/c/claude", "attach", "ffff6666"] }), ssh("gggg7777", { questa: true })];
const t = (argv, labels, address = "t5") => ({ address, argv, labels });
const b = {
  perArgv: bersaglio(t(["ssh", "-t", "amaltea", "/c/claude", "attach", "aaaa1111"]), sessioni),
  perEtichetta: bersaglio(t(["/bin/zsh", "-li"], { "arturo.sessione": "aaaa1111" }), sessioni),
  locale: bersaglio(t(["/c/claude", "attach", "bbbb2222"]), sessioni),
  senzaAttach: bersaglio(t(["/bin/zsh"], { "arturo.sessione": "cccc3333" }), sessioni),
  opzione: bersaglio(t(["/bin/zsh"], { "arturo.sessione": "dddd4444" }), sessioni),
  windows: bersaglio(t(["x"], { "arturo.sessione": "eeee5555" }), sessioni),
  nonSsh: bersaglio(t(["x"], { "arturo.sessione": "ffff6666" }), sessioni),
  diQui: bersaglio(t(["x"], { "arturo.sessione": "gggg7777" }), sessioni),
  shell: bersaglio(t(["/bin/zsh", "-li"]), sessioni),
  remotoHerdr: bersaglio(t(["ssh", "-t", "amaltea", "/c/claude", "attach", "aaaa1111"], null, "macbook/t5"), sessioni),
  nullo: bersaglio(null, sessioni),
  sconosciuta: bersaglio(t(["ssh", "-t", "amaltea", "/c/claude", "attach", "zzzz"]), sessioni),
};
const A = { target: "amaltea", macchina: "Amaltea" }, B = { target: "feder@torre", macchina: "Torre" };
const giro = [];
let st = null;
const fai = (nome, bers, adesso, spento) => { const r = passo(st, bers, adesso, spento); st = r.st; giro.push([nome, r.azione?.verbo ?? null, r.azione?.target ?? null, st?.target ?? null]); };
fai("niente", null, 0);
fai("fuoco", A, 1000);
fai("subito", A, 1000 + IN_AVVIO - 1);
fai("in avvio", A, 1000 + IN_AVVIO);
st = { ...st, stato: "attivo" };
fai("attivo presto", A, 4000 + RINNOVO - 2000);
fai("attivo rinnovo", A, 3000 + RINNOVO);
const visto = st.visto;
fai("via da poco", null, visto + RINNOVO - 1);
fai("via rinnovo", null, visto + RINNOVO);
fai("via troppo", null, visto + TENUTA + 1);
fai("spento da spento", null, visto + TENUTA + 2);
fai("riaccendo", A, 900000);
fai("cambio macchina", B, 900500);
fai("interruttore", B, 901000, true);
fai("interruttore fermo", B, 902000, true);
const righe = [rigaMicrofono(null), rigaMicrofono({ stato: "attivo", macchina: "Amaltea", qui: "MacBook Air" }), rigaMicrofono({ stato: "avvio", macchina: "Amaltea" }),
  rigaMicrofono({ stato: "errore", macchina: "Amaltea", motivo: "manca BlackHole" }), rigaMicrofono({ spento: true }), rigaMicrofono({ stato: "spento" })];
console.log(JSON.stringify({ b, giro, righe }));
"""


def hz63(repo: Path, casa: Path) -> str | None:
    import signal  # noqa: PLC0415
    mod = repo / "shared/volta/mods/arturo"
    script = mod / "volta_microfono.py"
    if not script.is_file() or not (mod / "microfono.js").is_file() or not (mod / "microfono.svg").is_file():
        return "nel mod mancano microfono.js, microfono.svg o volta_microfono.py"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, perche in (("cx.timer.every(OGNI_MICROFONO, (cx) => this.microfono(cx));", "volta.js non guarda il fuoco per il microfono"),
                          ("this.micScript = await esiste(`${appHome()}/mods/arturo/volta_microfono.py`);", "volta.js non cerca lo script del ponte nel mod"),
                          ('await exec(this.py, [this.micScript, "spegni"], { timeout: 20000 });', "all'avvio volta.js non chiude un ponte rimasto"),
                          ("passo(this.mic, spento ? null : bersaglio(t, this.dati?.sessioni), Date.now(), spento)", "volta.js non decide il ponte con passo() e bersaglio()"),
                          ('.on_click(() => setShared("arturo.microfono.spento", shared("arturo.microfono.spento") !== true))', "il clic sulla riga non spegne e riaccende il ponte"),
                          ('.when(Boolean(rigaMicrofono(shared("arturo.microfono"))), (el) =>', "l'elenco non mostra la riga del microfono")):
        if pezzo not in vj:
            return perche
    node = shutil.which("node")
    if node:
        copia = casa / "microfono.mjs"
        shutil.copyfile(mod / "microfono.js", copia)
        r = subprocess.run([node, "--input-type=module", "-e", PROVA_MICROFONO % json.dumps(copia.as_uri())],
                           capture_output=True, text=True, encoding="utf-8", timeout=30)
        if r.returncode != 0:
            return f"microfono.js non gira: {(r.stderr or r.stdout).strip()[:200]}"
        v = json.loads(r.stdout.strip().splitlines()[-1])
        ama, bal = {"target": "amaltea", "macchina": "Amaltea"}, {"target": "feder@torre", "macchina": "Torre"}
        atteso = {"perArgv": ama, "perEtichetta": ama, "locale": None, "senzaAttach": None, "opzione": None, "windows": bal,
                  "nonSsh": None, "diQui": None, "shell": None, "remotoHerdr": None, "nullo": None, "sconosciuta": None}
        if v["b"] != atteso:
            return f"bersaglio: atteso {atteso}, avuto {v['b']}"
        giro = [["niente", None, None, None], ["fuoco", "accendi", "amaltea", "amaltea"], ["subito", None, None, "amaltea"],
                ["in avvio", "accendi", "amaltea", "amaltea"], ["attivo presto", None, None, "amaltea"],
                ["attivo rinnovo", "accendi", "amaltea", "amaltea"], ["via da poco", None, None, "amaltea"],
                ["via rinnovo", "accendi", "amaltea", "amaltea"], ["via troppo", "spegni", None, None],
                ["spento da spento", None, None, None], ["riaccendo", "accendi", "amaltea", "amaltea"],
                ["cambio macchina", "accendi", "feder@torre", "feder@torre"], ["interruttore", "spegni", None, None],
                ["interruttore fermo", None, None, None]]
        if v["giro"] != giro:
            diverso = next((a, b) for a, b in zip(giro, v["giro"]) if a != b)
            return f"passo: atteso {diverso[0]}, avuto {diverso[1]}"
        righe = [None, {"testo": "Microfono: MacBook Air → Amaltea"}, {"testo": "Microfono: collego Amaltea…"},
                 {"testo": "Microfono: manca BlackHole (Amaltea)", "avviso": True},
                 {"testo": "Microfono: spento, le sessioni delle altre macchine sentono il loro"}, None]
        if v["righe"] != righe:
            return f"rigaMicrofono: avuto {v['righe']}"
    # volta_microfono.py con l'audio finto: un file JSON al posto di CoreAudio. Il ricevitore gira solo sui Mac
    # (BlackHole, SIGHUP e SIGTERM con il loro gestore): su Windows questa parte si salta, finché il ponte non
    # arriva lì (#5332).
    if os.name == "nt":
        return None
    cache, audio = casa / "mic-cache", casa / "audio.json"
    MIC, BH, ALTRO = "mic-vero", "BlackHole2ch_UID", "cuffie"
    ingressi = [{"uid": MIC, "nome": "Microfono"}, {"uid": BH, "nome": "BlackHole 2ch"}, {"uid": ALTRO, "nome": "Cuffie"}]
    beve = [sys.executable, "-c", "import sys\nwhile sys.stdin.buffer.read(4096): pass"]
    base = {k: v for k, v in os.environ.items() if not k.startswith("VOLTA_")}

    def amb(**altro):
        return {**base, "VOLTA_CACHE": str(cache), "VOLTA_MIC_AUDIO": str(audio), "VOLTA_MIC_SUONA": json.dumps(beve), **altro}

    def metti(uid, lista=ingressi):
        shutil.rmtree(cache, ignore_errors=True)
        audio.write_text(json.dumps({"predefinito": uid, "ingressi": lista}), encoding="utf-8")

    def ingresso():
        return json.loads(audio.read_text(encoding="utf-8"))["predefinito"]

    def ricevi(**altro):
        p = subprocess.Popen([sys.executable, str(script), "ricevi"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=amb(**altro))
        return p, json.loads(p.stdout.readline().decode("utf-8") or "{}")

    def fine(p, attesa=10):
        try:
            return p.wait(timeout=attesa)
        except subprocess.TimeoutExpired:
            p.kill()
            return None

    def comando(*argv, **altro):
        r = subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True, encoding="utf-8",
                           stdin=subprocess.DEVNULL, timeout=30, env=amb(**altro))
        try:
            return json.loads((r.stdout or "").strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {"rc": r.returncode, "uscita": (r.stdout + r.stderr)[:200]}

    # a fine flusso torna l'ingresso di prima
    metti(MIC)
    p, riga = ricevi()
    if riga.get("esito") != "attivo" or ingresso() != BH or not (cache / "microfono.json").is_file():
        fine(p, 0)
        return f"ricevi non mette il microfono virtuale: {riga}, ingresso {ingresso()}"
    # un secondo ponte è rifiutato e non tocca il primo
    p2, riga2 = ricevi()
    rc2 = fine(p2)
    if rc2 != 4 or riga2.get("motivo") != "microfono usato da un'altra macchina" or ingresso() != BH:
        fine(p, 0)
        return f"un secondo ponte non è rifiutato: rc {rc2}, {riga2}"
    p.stdin.write(b"\0" * 3200)
    p.stdin.close()
    if fine(p) != 0 or ingresso() != MIC or (cache / "microfono.json").exists():
        return f"a fine flusso l'ingresso non torna quello di prima: {ingresso()}"
    # su SIGTERM
    metti(MIC)
    p, riga = ricevi()
    p.send_signal(signal.SIGTERM)
    fine(p)
    if ingresso() != MIC or (cache / "microfono.json").exists():
        return f"su SIGTERM l'ingresso non torna quello di prima: {ingresso()}"
    # rete caduta: il flusso resta aperto ma non arriva più niente
    metti(MIC)
    p, riga = ricevi(VOLTA_MIC_SILENZIO="1")
    if fine(p, 6) != 0 or ingresso() != MIC:
        return "il ricevitore non chiude quando l'audio smette di arrivare"
    # senza BlackHole non tocca niente
    metti(MIC, [x for x in ingressi if x["uid"] != BH])
    p, riga = ricevi()
    if fine(p) != 3 or riga.get("motivo") != "manca BlackHole" or ingresso() != MIC or (cache / "microfono.json").exists():
        return f"senza BlackHole ricevi non si ferma pulito: {riga}"
    # un ingresso scelto a mano nel frattempo resta
    metti(MIC)
    p, riga = ricevi()
    audio.write_text(json.dumps({"predefinito": ALTRO, "ingressi": ingressi}), encoding="utf-8")
    p.stdin.close()
    fine(p)
    if ingresso() != ALTRO:
        return f"ricevi rimette l'ingresso di prima sopra una scelta fatta a mano: {ingresso()}"
    # ripara: solo se il ponte è morto
    morto = subprocess.Popen([sys.executable, "-c", "pass"])
    morto.wait()
    metti(BH)
    (cache).mkdir(parents=True, exist_ok=True)
    acceso = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "volta_microfono.py", "ricevi"])
    try:
        (cache / "microfono.json").write_text(json.dumps({"pid": acceso.pid, "prima": MIC, "virtuale": BH}), encoding="utf-8")
        if comando("ripara").get("esito") != "ponte vivo" or ingresso() != BH:
            return "ripara tocca un ponte vivo"
    finally:
        acceso.kill()
        acceso.wait()
    (cache / "microfono.json").write_text(json.dumps({"pid": morto.pid, "prima": MIC, "virtuale": BH}), encoding="utf-8")
    if comando("ripara").get("esito") != "riparato" or ingresso() != MIC or (cache / "microfono.json").exists():
        return f"ripara non rimette l'ingresso dopo un ponte morto: {ingresso()}"
    # un ponte morto male non blocca il prossimo: ricevi ripara e parte
    metti(BH)
    (cache).mkdir(parents=True, exist_ok=True)
    (cache / "microfono.json").write_text(json.dumps({"pid": morto.pid, "prima": MIC, "virtuale": BH}), encoding="utf-8")
    p, riga = ricevi()
    p.stdin.close()
    fine(p)
    if riga.get("esito") != "attivo" or riga.get("prima") != MIC or ingresso() != MIC:
        return f"dopo un ponte morto male ricevi non riparte dall'ingresso vero: {riga}, {ingresso()}"
    # lato locale: accendi, rinnova, spegni, scadenza
    zeri = [sys.executable, "-c", "import sys, time\nwhile True:\n    sys.stdout.buffer.write(bytes(3200)); sys.stdout.buffer.flush(); time.sleep(0.1)"]
    finti = {"VOLTA_MIC_CATTURA": json.dumps(zeri), "VOLTA_MIC_SSH": json.dumps([sys.executable, str(script), "ricevi"])}

    def aspetta(cosa, secondi=8):
        fino = time.time() + secondi
        while time.time() < fino:
            if cosa():
                return True
            time.sleep(0.2)
        return False
    metti(MIC)
    try:
        primo = comando("accendi", "amaltea", **finti)
        if primo.get("stato") != "avvio":
            return f"accendi non parte: {primo}"
        if not aspetta(lambda: comando("stato", **finti).get("locale", {}).get("stato") == "attivo" and ingresso() == BH):
            return f"il ponte locale non arriva ad attivo: {comando('stato', **finti)}, ingresso {ingresso()}"
        pid = json.loads((cache / "microfono-locale.json").read_text(encoding="utf-8"))["pid"]
        if comando("accendi", "amaltea", **finti).get("stato") != "attivo" or json.loads((cache / "microfono-locale.json").read_text(encoding="utf-8"))["pid"] != pid:
            return "un secondo accendi sullo stesso bersaglio apre un altro ponte invece di rinnovarlo"
        if comando("spegni", **finti).get("stato") != "spento" or not aspetta(lambda: ingresso() == MIC):
            return f"spegni non chiude il ponte: ingresso {ingresso()}"
        # senza rinnovo il ponte scade da solo
        corta = {**finti, "VOLTA_MIC_SCADENZA": "1.5"}
        comando("accendi", "amaltea", **corta)
        if not aspetta(lambda: ingresso() == BH):
            return "il ponte con la scadenza corta non parte"
        if not aspetta(lambda: ingresso() == MIC and comando("stato", **corta).get("locale", {}).get("stato") == "spento"):
            return f"senza rinnovo il ponte non scade: {comando('stato', **corta)}, ingresso {ingresso()}"
        # un errore dell'altra macchina arriva in chiaro
        metti(MIC, [x for x in ingressi if x["uid"] != BH])
        comando("accendi", "amaltea", **finti)
        if not aspetta(lambda: comando("stato", **finti).get("locale", {}).get("motivo") == "manca BlackHole"):
            return f"l'errore dell'altra macchina non arriva: {comando('stato', **finti)}"
    finally:
        comando("spegni", **finti)
    return None


def hz65(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    mod = repo / "shared/volta/mods/arturo"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_NASCI, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    attach = ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]
    riga = "ssh -t %s torre.lan claude attach ffff1111" % " ".join(OPZIONI_SSH)
    nascita = ["/bin/zsh", "-lic", '"$@"; exec "$0" -li', "/bin/zsh", *attach]
    viva = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 77, "argv": attach}}
    nuda = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 10, "argv": ["/bin/zsh", "-li"]}}
    spazio = {"id": "s1", "name": "progetto-x", "active": True, "tabs": [{"id": "tb0", "name": "Shell"}, {"id": "tb1", "name": "Progetto x", "active": True}]}
    herdr = {"spaces": [spazio], "panes": [{"terminal": "t3", "tab": "tb0"}, {"terminal": "t7", "tab": "tb1"}],
             "terminals": [{"address": "t3", "argv": ["zsh"]}, {"address": "t7", "argv": nascita}]}
    riga_s = lambda ident, host: {"id": ident, "sessionId": ident + "-aaaa", "host": host, "macchina": host, "questa": False,  # noqa: E731
                                  "nome": "Progetto x", "progetto": "progetto-x", "stato": "ferma", "tipo": "background",
                                  "attach": ["ssh", "-t", host.lower() + ".lan", "claude", "attach", ident]}
    # HZ_APP non è ~/.config/herdr-app della casa: per cacheVolta() di dati.js è una finestra di prova,
    # che legge l'elenco in <cartella di Herdr>/cache/volta (#5449)
    cache = app / "cache/volta"
    cache.mkdir(parents=True)
    elenco = cache / "sessioni.json"
    # la sessione della scheda non è la prima dell'elenco: si cerca per id
    note = json.dumps({"sessioni": [riga_s("aaaa2222", "Studio"), riga_s("ffff1111", "Torre")]})

    def volta(caso, letture, herdr=herdr, uscita='{"ok": true}', sessioni=note):
        elenco.write_text(sessioni, encoding="utf-8")
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso, "HZ_EXEC": uscita,
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": [], "arturo.dove": "qui"}),
             "HZ_HERDR": json.dumps(herdr), "HZ_HC_GET": json.dumps(letture)}
        for k in ("HZ_NASCE", "HZ_STATO", "HZ_PRONTA", "HZ_HC_ROTTO", "HZ_HC_READ"):
            e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    invii = lambda v: [x for x in v["inviati"] if x[0] == "send"]  # noqa: E731
    sonda = lambda v: [x[2:] for x in v["eseguiti"] if len(x) > 2 and x[2] == "apri"]  # noqa: E731
    todo = "Lavoriamo sul todo #42: Prova"
    try:
        # la scheda è tornata alla shell: il testo non parte, la sessione riparte lì e l'avviso lo dice.
        # Letture: prima di scrivere (nuda), in apriSessione (nuda), nella veglia (Claude è tornato).
        for caso, cosa in (("lavoraci", "Lavoraci"), ("ricorda", "Ricordami una cosa")):
            v = volta(caso, {"t7": [nuda, nuda, viva]})
            if invii(v) != [["send", "t7", riga]]:
                return f"{cosa} con la scheda tornata alla shell: nella shell finisce {invii(v)}, atteso solo il rilancio di claude attach"
            if sonda(v) != [["apri", "Torre", "ffff1111"]]:
                return f"{cosa} con la scheda tornata alla shell non riapre la sessione della scheda: {sonda(v)}"
            if len(v["avvisi"]) != 1 or "riaperto" not in v["avvisi"][0].get("title", "") or "Riprova" not in v["avvisi"][0].get("body", ""):
                return f"{cosa} con la scheda tornata alla shell non dice di riprovare: {v['avvisi']}"
            if any(x["cmd"] in ("tab.new", "space.new") for x in v["lanciati"]):
                return f"{cosa}: la sessione riparte in una scheda nuova invece che nella sua: {v['lanciati']}"
        # Volta non elenca più la sessione: niente nella shell, e lo si dice
        v = volta("lavoraci", {"t7": [nuda]}, sessioni=json.dumps({"sessioni": [riga_s("aaaa2222", "Studio")]}))
        if invii(v) or sonda(v) or len(v["avvisi"]) != 1 or "chiusa" not in v["avvisi"][0].get("title", ""):
            return f"una scheda tornata alla shell senza sessione nell'elenco: {invii(v)}, {sonda(v)}, {v['avvisi']}"
        v = volta("lavoraci", {"t7": [nuda]}, sessioni="non è json")
        if invii(v) or len(v["avvisi"]) != 1 or "chiusa" not in v["avvisi"][0].get("title", ""):
            return f"con sessioni.json illeggibile il testo va nella shell, o non si dice niente: {invii(v)}, {v['avvisi']}"
        # il servizio non parte: niente nella shell, l'avviso porta il motivo
        v = volta("lavoraci", {"t7": [nuda]}, uscita=json.dumps({"errore": "il servizio di Claude non parte su Torre: spenta"}))
        if invii(v) or len(v["avvisi"]) != 1 or "spenta" not in v["avvisi"][0].get("body", "") or v["avvisi"][0].get("level") != "error":
            return f"la sessione che non si riapre: {invii(v)}, {v['avvisi']}"
        # Claude gira nella scheda: il testo parte come prima, senza avvisi e senza servizio
        v = volta("lavoraci", {"t7": [viva]})
        if invii(v) != [["send", "t7", todo]] or v["avvisi"] or sonda(v):
            return f"con Claude nella scheda il testo del todo non parte: {invii(v)}, {v['avvisi']}"
        v = volta("ricorda", {"t7": [viva]})
        if len(invii(v)) != 1 or invii(v)[0][:2] != ["send", "t7"] or "todo" not in invii(v)[0][2] or v["avvisi"]:
            return f"con Claude nella scheda il suggerimento non parte: {invii(v)}, {v['avvisi']}"
        # un agente di Herdr: lo stato lo dice Herdr, la scheda non si interroga
        agente = {**herdr, "agents": [{"space": "s1", "tab": "tb1", "address": "t7", "status": "idle"}]}
        v = volta("lavoraci", {"t7": [nuda]}, herdr=agente)
        if v["inviati"] != [["send", "t7", todo]] or v["avvisi"]:
            return f"con un agente di Herdr il testo non parte come prima: {v['inviati']}, {v['avvisi']}"
        v = volta("ricorda", {"t7": [nuda]}, herdr=agente)
        if len(v["inviati"]) != 1 or v["inviati"][0][:2] != ["send", "t7"] or v["avvisi"]:
            return f"con un agente di Herdr il suggerimento non parte come prima: {v['inviati']}, {v['avvisi']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    return None

PROVA_NASCITA = r"""
import { nuova, inNascita } from "./dati.mjs";
import { eseguiti, avvisi, nascite, lanciati, shared } from "./herdr.mjs";
const prima = inNascita();
const esito = await nuova("ciao Volta");
console.log(JSON.stringify({ prima, esito: esito ?? null, eseguiti, avvisi, nascite, lanciati, dopo: shared("arturo.nascita") ?? null }));
"""


def hz66(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    mod = repo / "shared/volta/mods/arturo"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_NASCITA, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    attach = ["claude", "attach", "ffff1111"]
    nata = json.dumps({"id": "ffff1111", "sessionId": "ffff1111-aaaa", "attach": attach})
    adesso = int(time.time() * 1000)
    minuti = lambda n: {"macchina": "Torre", "da": adesso - int(n * 60000)}  # noqa: E731

    def volta(nascita, herdr=None, **extra):
        condivisi = {"arturo.volta.macchine": [], "arturo.dove": "qui"}
        if nascita is not None:
            condivisi["arturo.nascita"] = nascita
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_EXEC": nata,
             "HZ_SHARED": json.dumps(condivisi), "HZ_HERDR": json.dumps(herdr or {}), **extra}
        for k in ("HZ_NASCE", "HZ_STATO", "HZ_PRONTA", "HZ_HC_ROTTO", "HZ_HC_READ", "HZ_HC_GET", "HZ_CASO"):
            if k not in extra:
                e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    nasce = lambda v: bool(v["eseguiti"]) and v["eseguiti"][0][2:] == ["nasci", "qui", "--", "ciao Volta"]  # noqa: E731
    try:
        # nessuna nascita in corso: durante la sonda il segno dice dove e da quando, poi sparisce
        v = volta(None)
        if v["prima"] is not None or not nasce(v) or v["esito"] != {"ok": True, "id": "ffff1111"}:
            return f"una nascita senza altre in corso: {v['prima']}, {v['eseguiti']}, {v['esito']}"
        segno = v["nascite"][0] if v["nascite"] else None
        if not isinstance(segno, dict) or segno.get("macchina") != "qui" or not isinstance(segno.get("da"), (int, float)) \
                or abs(segno["da"] - adesso) > 120000:
            return f"durante la nascita arturo.nascita non dice macchina e ora: {segno}"
        if v["dopo"] is not None:
            return f"a nascita finita arturo.nascita resta: {v['dopo']}"
        # una nascita rimasta a metà (finestra chiusa, Volta chiusa): dopo 7 minuti non vale più
        for cosa, vecchia in (("vecchia di 8 minuti", minuti(8)), ("scritta come stringa dalla versione di prima", "Torre"),
                              ("senza ora", {"macchina": "Torre"}), ("con un'ora che non è un numero", {"macchina": "Torre", "da": "ieri"})):
            v = volta(vecchia)
            if v["prima"] is not None or not nasce(v) or v["avvisi"]:
                return f"una nascita {cosa} blocca ancora le altre: {v['prima']}, {v['eseguiti']}, {v['avvisi']}"
            if v["dopo"] is not None:
                return f"dopo una nascita partita sopra una {cosa} il segno resta: {v['dopo']}"
        # una nascita fresca rifiuta la seconda, lo dice e lascia il segno dell'altra. 6 minuti e mezzo:
        # la sonda ne aspetta 6, il segno deve durare di più
        for n in (1, 6.5):
            fresca = minuti(n)
            v = volta(fresca)
            if v["prima"] != "Torre" or v["eseguiti"] or v["lanciati"]:
                return f"con una nascita di {n} minuti fa ne parte un'altra: {v['prima']}, {v['eseguiti']}"
            if len(v["avvisi"]) != 1 or "già nascendo" not in v["avvisi"][0].get("title", "") or "errore" not in (v["esito"] or {}):
                return f"la nascita rifiutata non lo dice: {v['avvisi']}, {v['esito']}"
            if v["dopo"] != fresca:
                return f"la nascita rifiutata toglie il segno dell'altra: {v['dopo']}"
        # la sessione nasce ma la sua scheda non si apre: un avviso, e il segno sparisce
        nascita = ["/bin/zsh", "-lic", '"$@"; exec "$0" -li', "/bin/zsh", *attach]
        nuda = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 10, "argv": ["/bin/zsh", "-li"]}}
        herdr = {"spaces": [{"id": "s1", "name": "Volta", "tabs": [{"id": "tb1", "active": True}]}],
                 "panes": [{"terminal": "t7", "tab": "tb1"}], "terminals": [{"address": "t7", "argv": nascita}]}
        v = volta(None, herdr=herdr, HZ_HC_GET=json.dumps({"t7": [nuda]}), HZ_HC_ROTTO="send")
        if len(v["avvisi"]) != 1 or "non si apre" not in v["avvisi"][0].get("title", "") or "errore" not in (v["esito"] or {}):
            return f"una sessione nata che non si apre non lo dice: {v['avvisi']}, {v['esito']}"
        if v["dopo"] is not None:
            return f"dopo una nascita finita male il segno resta: {v['dopo']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    if "const nascita = inNascita();" not in (mod / "comuni.js").read_text(encoding="utf-8"):
        return "la riga Nasce su legge arturo.nascita senza la scadenza (inNascita)"
    return None


PROVA_COMANDI = r"""
const { instrada, comandoApri, comandoSuggerimento, daRimandare, PING } = await import(%s);
const v = (c) => { const i = instrada(c); return [i.verbo, i.arg, i.lungo]; };
const comandi = %s;
console.log(JSON.stringify({
  tabella: Object.fromEntries(comandi.map((c) => [c, v(c)])),
  apri: comandoApri("due-mondi"), giroApri: v(comandoApri("due-mondi").slice(7)),
  sug: comandoSuggerimento("trova"), giroSug: v(comandoSuggerimento("trova").slice(7)),
  ping: PING, niente: [v(undefined), v(null)],
  rimanda: comandi.concat([PING]).filter((c) => daRimandare(c, true)),
  mostrata: comandi.concat([PING]).filter((c) => daRimandare(c, false)),
}));
"""

# comando → [verbo, argomento, lungo]
COMANDI = {
    "apri": ["apri", None, False], "apri-due-mondi": ["progetto", "due-mondi", True], "apri-": ["progetto", "", True],
    "chiedi": ["chiedi", None, False], "suggerimento-trova": ["suggerimento", "trova", True],
    "settimana": ["settimana", None, False], "guida": ["guida", 0, False], "guida3": ["guida", 2, False],
    "nuova": ["nuova", None, True], "dove-qui": ["dove", "qui", False], "dove-Torre": ["dove", "Torre", False],
    "nota": ["nota", None, True], "nota-n12": ["nota", "n12", True], "note": ["note", None, False],
    "versione": ["versione", None, False], "volta-gruppi-macchina": ["gruppi", "macchina", False],
    "volta-gruppi-progetto": ["gruppi", "progetto", False], "volta-nuova": ["volta-nuova", None, True],
    "casa": ["casa", None, False], "casa-chiudi": ["casa-chiudi", None, False],
    "volta-menu-ab12": ["volta-menu", "ab12", False], "volta-altro-ab12": ["volta-altro", "ab12", False],
    "volta-cambia-nome-6162-ab12": ["volta-cambia", "volta-cambia-nome-6162-ab12", False],
    "volta-gesto-stop-ab12": ["volta-gesto", {"verbo": "stop", "id": "ab12"}, False],
    "volta-gesto-rm-pid-77": ["volta-gesto", {"verbo": "rm", "id": "pid-77"}, False],
    "volta-ab12": ["volta", "ab12", False], "volta-gesto-": ["volta", "gesto-", False],
    "nuova-00630069": ["nuova", "00630069", True], "nuova-zz": [None, None, False], "nuova-006": [None, None, False],
    "boh": [None, None, False], "": [None, None, False],
}


def comandi_node(repo: Path, casa: Path) -> dict | str | None:
    """comandi.js con node: la tabella di instrada() e chi si rimanda a barra nascosta."""
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "comandi.mjs"
    shutil.copyfile(repo / "shared/volta/mods/arturo/comandi.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_COMANDI % (json.dumps(copia.as_uri()), json.dumps(list(COMANDI)))],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"comandi.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def hz67(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    testi = {n: (mod / n).read_text(encoding="utf-8") for n in ("apri.js", "revisione.js", "suggerimenti.js", "testata.js", "barra.js")}
    # le finestre mandano il comando e si chiudono: un overlay chiuso ferma il suo codice al primo await
    for nome in ("apri.js", "revisione.js", "suggerimenti.js", "testata.js"):
        m = re.search(r"await\s+(apri|esegui|chiedi|nuova|nuovaScheda)\(", testi[nome])
        if m:
            return f"{nome} aspetta {m.group(1)}() dentro una parte che può chiudersi: la nascita resta a metà"
    attesi = (
        ("apri.js", "    if (r.tipo === \"sessione\") run(`arturo.volta-${chiaveSessione(r.s)}`);\n    else if (r.tipo === \"progetto\") run(comandoApri(slug(r.nome)));\n    else if (r.tipo === \"nuova\" && r.testo) run(comandoNuova(r.testo));\n    else return;\n    this.chiudi();", "Cerca non manda il comando alla barra"),
        ("revisione.js", ".on_click(() => { run(comandoApri(k)); this.chiudi(); })", "Fai il punto non manda il comando alla barra"),
        ("suggerimenti.js", '.on_click(() => { if (sug.dove === "apri") apriFinestra(); else run(comandoSuggerimento(sug.id)); dopo?.(); })',
         "una richiesta di Cosa posso chiedere non manda il comando alla barra"),
        ("testata.js", 'pulsante("b-nuova", "square-pen", "Nuova richiesta", () => run("arturo.nuova"),', "Nuova richiesta del benvenuto non manda il comando alla barra"),
        ("barra.js", "        try { this.comando(instrada(c), cx); } catch (e) { this.rotto(c, e); }\n", "il ciclo dei comandi non ha il try: un comando rotto ferma la barra"),
        ("barra.js", "      try { await lavoro(); } catch (e) { this.rotto(c, e); }\n", "un comando lungo che si rompe non lo dice"),
        ("barra.js", 'else if (c === "progetto") { if (arg) this.lungo(c, cx, () => apri(arg)); }', "barra.js non apre il progetto di arturo.apri-<slug>"),
        ("barra.js", 'else if (c === "suggerimento") { const s = SUGGERIMENTI.find((x) => x.id === arg); if (s) this.lungo(c, cx, () => esegui(s)); }',
         "barra.js non esegue arturo.suggerimento-<id>"),
        ("barra.js", 'else if (c === "nuova") this.lungo(c, cx, () => (arg ? nuova(decodifica(arg)) : nuova()));', "arturo.nuova non parte come comando lungo"),
        ("barra.js", 'else if (c === "volta-nuova") this.lungo(c, cx, () => nuovaScheda());', "arturo.volta-nuova non parte come comando lungo"),
        ("barra.js", 'else if (c === "nota") this.lungo(c, cx, () => apriNota(arg));', "arturo.nota non parte come comando lungo"),
    )
    for file, pezzo, motivo in attesi:
        if pezzo not in testi[file]:
            return f"{file}: {motivo}"
    # il ciclo non aspetta nessun comando: l'unico await è la lettura del comando dopo
    bj = testi["barra.js"]
    ciclo = bj.split("        const c = await nextCommand();\n", 1)[-1].split("\n    });\n", 1)[0]
    corpo = bj.split("  comando({ verbo, arg }, cx) {\n", 1)[-1].split("\n  }\n", 1)[0]
    if "await" in ciclo or "await" in corpo:
        return "barra.js aspetta un comando dentro il ciclo: una nascita di sei minuti tiene in coda i comandi dopo"
    d = comandi_node(repo, casa)
    if d is None or isinstance(d, str):
        return d
    for c, atteso in COMANDI.items():
        if d["tabella"].get(c) != atteso:
            return f"instrada({c!r}) dà {d['tabella'].get(c)}, atteso {atteso}"
    if d["apri"] != "arturo.apri-due-mondi" or d["giroApri"] != ["progetto", "due-mondi", True]:
        return f"comandoApri e instrada non si parlano: {d['apri']}, {d['giroApri']}"
    if d["sug"] != "arturo.suggerimento-trova" or d["giroSug"] != ["suggerimento", "trova", True]:
        return f"comandoSuggerimento e instrada non si parlano: {d['sug']}, {d['giroSug']}"
    if d["niente"] != [[None, None, False], [None, None, False]]:
        return f"instrada senza comando: {d['niente']}"
    return None


def hz68(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    testi = {n: (mod / n).read_text(encoding="utf-8") for n in ("testata.js", "barra.js")}
    attesi = (
        ("testata.js", "        const c = await nextCommand();\n        try { await this.rimanda(c, cx); } catch {", "la barra di stato non legge i comandi"),
        ("testata.js", '    if (!daRimandare(c, Boolean(trova(layout(), "sidebar")?.hidden))) return;\n', "la barra di stato agisce anche con la barra mostrata"),
        ("testata.js", '    run("layout.toggle", { id: "sidebar" });\n', "la barra di stato non mostra la barra nascosta"),
        ("testata.js", "      run(`arturo.${PING}`);\n", "la barra di stato non chiede alla barra se riceve i comandi"),
        ("testata.js", '      if (Number(shared("arturo.barra.viva")) >= da) return run(`arturo.${c}`);\n', "la barra di stato non rimanda il comando quando la barra risponde"),
        ("barra.js", '    if (c === "ci-sei") setShared("arturo.barra.viva", Date.now());\n', "la barra non risponde al comando di controllo"),
    )
    for file, pezzo, motivo in attesi:
        if pezzo not in testi[file]:
            return f"{file}: {motivo}"
    tj = testi["testata.js"]
    corpo = tj.split("  async rimanda(c, cx) {\n", 1)[-1].split("\n  }\n", 1)[0]
    if corpo.index("daRimandare(") > corpo.index('run("layout.toggle"') or corpo.index("const da = Date.now();") > corpo.index('run("layout.toggle"'):
        return "testata.js: la barra si mostra prima di guardare se è nascosta, o l'ora si prende dopo"
    d = comandi_node(repo, casa)
    if d is None or isinstance(d, str):
        return d
    attesi_rimanda = [c for c, v in COMANDI.items() if v[0] is not None]
    if d["ping"] != "ci-sei" or d["rimanda"] != attesi_rimanda:
        return f"a barra nascosta si rimandano {d['rimanda']}, attesi i comandi noti senza quello di controllo"
    if d["mostrata"]:
        return f"a barra mostrata la barra di stato rimanda {d['mostrata']}: il comando partirebbe due volte"
    return None


# L'hc finto del lotto 4: HZ_HC è { macchine, ls: {dorme, rc, out}, exec: { <macchina>: { <programma>: {out, rc, dorme} } } }.
# Segna ogni chiamata in HZ_HC_LOG, con --timeout e la riga di codice com'erano.
HC_LENTO = r"""
import json, os, sys, time
conf = json.loads(os.environ["HZ_HC"])
a = sys.argv[1:]
with open(os.environ["HZ_HC_LOG"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(a) + "\n")
if a[:2] == ["machine", "ls"]:
    ls = conf.get("ls", {})
    time.sleep(ls.get("dorme", 0))
    print(ls["out"] if "out" in ls else json.dumps({"machines": conf.get("macchine", [])}))
    sys.exit(ls.get("rc", 0))
if a[:2] == ["exec", "--on"]:
    nome = a[2]
    if "--timeout" in a[:6]:
        i = a.index("--timeout"); del a[i:i + 2]
    v = conf.get("exec", {}).get(nome, {}).get(a[3])
    if v is None:
        print(json.dumps({"error": {"kind": "spawn_failed", "message": "cannot start %s" % a[3]}})); sys.exit(1)
    time.sleep(v.get("dorme", 0))
    print(v.get("out", "")); sys.exit(v.get("rc", 0))
sys.exit(2)
"""

# Il claude finto del lotto 4. HZ_AGENTI: "avviso" (una riga prima del JSON), "rotto" (esce 1), "sporco"
# (esce 0 senza elenco), "dorme" (non risponde per 12 s), "tardi" (elenca la sessione dalla seconda chiamata,
# contate in HZ_CONTA). HZ_SESSIONI è l'elenco in JSON.
CLAUDE_FINTO_LOTTO4 = r"""#!/usr/bin/env python3
import json, os, sys, time
modo = os.environ.get("HZ_AGENTI", "")
if sys.argv[1:2] == ["--bg"]:
    print("backgrounded \u00b7 abcd1234\n  claude attach abcd1234    open in this terminal")
    sys.exit(0)
if sys.argv[1:2] == ["daemon"]:
    print("control.sock: reachable"); sys.exit(0)
if sys.argv[1:2] == ["agents"]:
    if modo == "dorme":
        time.sleep(12)
    if modo == "rotto":
        print("boom: il servizio non risponde", file=sys.stderr); sys.exit(1)
    if modo == "sporco":
        print("niente da vedere [qui]"); sys.exit(0)
    elenco = json.loads(os.environ.get("HZ_SESSIONI", "[]"))
    if modo == "tardi":
        f = os.environ["HZ_CONTA"]
        n = int(open(f).read() or 0) + 1 if os.path.exists(f) else 1
        open(f, "w").write(str(n))
        if n < 2:
            elenco = []
    if modo in ("avviso", "tardi"):
        print("Warning: [beta] a newer version is available")
    print(json.dumps(elenco))
"""


def lotto4(casa: Path, conf: dict, hc_finto: str = HC_LENTO) -> tuple[dict, Path, Path]:
    """L'ambiente dei casi della sonda: hc finto, claude finto nel PATH, cartella di Claude vuota."""
    finto = casa / "hc_lento.py"
    finto.write_text(hc_finto, encoding="utf-8")
    bindir = casa / "bin"
    bindir.mkdir(exist_ok=True)
    cl = bindir / "claude"
    cl.write_text(CLAUDE_FINTO_LOTTO4, encoding="utf-8")
    os.chmod(cl, 0o755)
    (casa / "conf").mkdir(exist_ok=True)
    log = casa / "hc.log"
    env = {**os.environ, "HZ_HC": json.dumps(conf), "VOLTA_HC": json.dumps([sys.executable, str(finto)]), "HZ_HC_LOG": str(log),
           "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", "CLAUDE_CONFIG_DIR": str(casa / "conf"), "PYTHONIOENCODING": "utf-8",
           "HERDR_APP_HOME": str(casa / "app")}
    for k in ("VOLTA_SONDA_LOCALE", "VOLTA_ATTESA_LETTURA", "HZ_AGENTI", "HZ_SESSIONI", "HZ_CONTA"):
        env.pop(k, None)
    return env, log, casa / "sessioni.json"


def hz69(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    sonda = mod / "volta_sonda.py"
    import ast  # noqa: PLC0415
    testo = sonda.read_text(encoding="utf-8")
    costanti = {n.targets[0].id: n.value.value for n in ast.parse(testo).body
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and isinstance(n.value, ast.Constant)}
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    m = re.search(r'\[this\.script, "volta", "--scrivi", this\.file\], \{ timeout: (\d+) \}', volta)
    if not m:
        return "volta.js (aggiorna) non lancia più la lettura con un'attesa sua"
    tetto = costanti.get("ATTESA_LETTURA")
    if not isinstance(tetto, int) or tetto * 1000 > int(m.group(1)) - 10000:
        return f"la lettura ha un tetto di {tetto} s, ma volta.js la taglia a {m.group(1)} ms: servono 10 s di margine"
    sessione = lambda sid, **k: dict({"sessionId": sid, "kind": "background", "state": "done"}, **k)  # noqa: E731
    conf = {"macchine": [{"name": "Svelta", "target": "svelta", "state": "connected"},
                         {"name": "Lenta", "target": "lenta", "state": "connected"}],
            "exec": {"Svelta": {"python3": {"out": json.dumps({"claude": "/s/claude", "sessioni": [sessione("ssss1111-s")]})}},
                     "Lenta": {"python3": {"dorme": 20, "out": json.dumps({"claude": "/l/claude", "sessioni": [sessione("llll1111-l")]})}}}}
    env, log, uscita = lotto4(casa, conf)
    env["VOLTA_SONDA_LOCALE"] = json.dumps({"claude": "/q/claude", "sessioni": [sessione("aaaa1111-q")]})
    env["VOLTA_ATTESA_LETTURA"] = "7"
    uscita.write_text(json.dumps({"letto": "prima", "macchine": [{"host": "qui", "questa": True}, {"host": "Lenta"}], "sessioni": [
        {"host": "Lenta", "id": "llll0000", "sessionId": "llll0000-l"}]}), encoding="utf-8")
    da = time.monotonic()
    try:
        r = subprocess.run([sys.executable, str(sonda), "volta", "--scrivi", str(uscita)], capture_output=True, text=True, timeout=14, env=env)
    except subprocess.TimeoutExpired:
        return "con una macchina che non risponde la lettura non finisce entro il tetto (7 s, attesi al più 14)"
    durata = time.monotonic() - da
    if r.returncode != 0:
        return f"volta_sonda.py esce {r.returncode}: {(r.stderr or r.stdout).strip()[-160:]}"
    if durata > 8.5:
        return f"la lettura dura {durata:.1f} s con un tetto di 7"
    d = json.loads(uscita.read_text(encoding="utf-8"))
    if d.get("letto") == "prima":
        return "il documento non è stato riscritto"
    lenta = next((x for x in d["macchine"] if x["host"] == "Lenta"), None)
    if not lenta or "non ha risposto in" not in str(lenta.get("irraggiungibile")):
        return f"la macchina lenta non è segnata irraggiungibile col motivo: {lenta}"
    if "exec" in str(lenta.get("irraggiungibile")) or len(str(lenta.get("irraggiungibile"))) > 60:
        return f"il motivo della macchina lenta porta il comando: {lenta['irraggiungibile'][:80]}"
    per = {x["id"]: x for x in d["sessioni"]}
    if set(per) != {"aaaa1111", "ssss1111", "llll0000"} or not per["llll0000"].get("vecchia") or per["ssss1111"].get("vecchia"):
        return f"sessioni {sorted(per)}: attese quella di qui, quella della macchina svelta e la vecchia della lenta"
    # hc exec e la sonda sulla macchina ricevono i secondi che restano
    chiamate = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    for c in (x for x in chiamate if x[:2] == ["exec", "--on"]):
        if "--timeout" not in c:
            return f"hc exec verso {c[2]} parte senza --timeout: Herdr lo terrebbe aperto oltre il tetto"
        entro = int(c[c.index("--timeout") + 1])
        dentro = re.match(r"T=(\d+);", c[-1])
        if not 1 <= entro <= 7 or not dentro or not 1 <= int(dentro.group(1)) <= entro:
            return f"hc exec verso {c[2]}: --timeout {entro}, sonda {c[-1][:12]!r}: attesi i secondi che restano, al più 7"
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    # dentro la sonda claude agents non aspetta oltre i secondi ricevuti
    sp = importlib_spec("volta_sonda_hz69", sonda)
    da = time.monotonic()
    try:
        r = subprocess.run([sys.executable, "-c", "T = 3\n" + sp.SONDA], capture_output=True, text=True, timeout=20, env={**env, "HZ_AGENTI": "dorme"})
    except subprocess.TimeoutExpired:
        return "la sonda con 3 secondi a disposizione non torna in 20"
    if time.monotonic() - da > 9:
        return f"la sonda con 3 secondi a disposizione aspetta claude agents {time.monotonic() - da:.0f} s"
    try:
        errore = json.loads(r.stdout.strip().splitlines()[-1]).get("errore")
    except (ValueError, IndexError):
        errore = None
    if not errore or "tempo" not in errore:
        return f"claude agents fuori tempo: la sonda non lo dice ({(r.stdout + r.stderr).strip()[-120:]})"
    return None


def importlib_spec(nome: str, file: Path):
    import importlib.util  # noqa: PLC0415
    sp = importlib.util.spec_from_file_location(nome, file)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def hz70(repo: Path, casa: Path) -> str | None:
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    if '"~/.local/bin/hc" + (".exe" if os.name == "nt" else "")' not in sonda.read_text(encoding="utf-8"):
        return "su Windows hc() ripiega su ~/.local/bin/hc senza .exe"
    sessione = lambda sid, **k: dict({"sessionId": sid, "kind": "background", "state": "done"}, **k)  # noqa: E731
    prima = {"letto": "prima", "macchine": [{"macchina": "Questa", "host": "qui", "questa": True}, {"macchina": "Studio", "host": "Studio", "questa": False}],
             "sessioni": [{"host": "Studio", "id": "bbbb1111", "sessionId": "bbbb1111-s"}, {"host": "qui", "id": "vvvv0000", "sessionId": "vvvv0000-q"}]}
    studio = {"macchine": [{"name": "Studio", "target": "studio", "state": "connected"}],
              "exec": {"Studio": {"python3": {"out": json.dumps({"claude": "/s/claude", "sessioni": [sessione("bbbb2222-s")]})}}}}

    def leggi(ls, tetto="9", hc=None):
        cartella = casa / f"giro{len(list(casa.glob('giro*')))}"
        cartella.mkdir()
        env, _log, uscita = lotto4(cartella, dict(studio, ls=ls))
        env["VOLTA_SONDA_LOCALE"] = json.dumps({"claude": "/q/claude", "sessioni": [sessione("aaaa1111-q")]})
        env["VOLTA_ATTESA_LETTURA"] = tetto
        if hc:
            env["VOLTA_HC"] = hc
        uscita.write_text(json.dumps(prima), encoding="utf-8")
        r = subprocess.run([sys.executable, str(sonda), "volta", "--scrivi", str(uscita)], capture_output=True, text=True, timeout=30, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"volta_sonda.py esce {r.returncode}: {(r.stderr or r.stdout).strip()[-160:]}")
        return json.loads(uscita.read_text(encoding="utf-8")), env

    try:
        # Herdr risponde: Studio si legge, le righe sono nuove
        d, env = leggi({})
        per = {x["id"]: x for x in d["sessioni"]}
        if [m["host"] for m in d["macchine"]] != ["qui", "Studio"] or set(per) != {"aaaa1111", "bbbb2222"}:
            return f"con Herdr che risponde: macchine {[m['host'] for m in d['macchine']]}, sessioni {sorted(per)}"
        # Herdr non dice le macchine: restano quelle di prima, con le loro righe segnate vecchie
        for cosa, ls in (("esce 1", {"rc": 1, "out": "core non raggiungibile"}), ("risponde altro", {"out": "non sono JSON"}),
                         ("risponde un elenco che non è un elenco", {"out": json.dumps({"machines": "nessuna"})}),
                         ("non fa in tempo", {"dorme": 8})):
            d, _ = leggi(ls, "6" if "dorme" in ls else "9")
            studio_ = next((m for m in d["macchine"] if m["host"] == "Studio"), None)
            if not studio_ or "Herdr" not in str(studio_.get("irraggiungibile")):
                return f"hc machine ls {cosa}: la macchina di prima sparisce o non dice perché ({d['macchine']})"
            per = {x["id"]: x for x in d["sessioni"]}
            if set(per) != {"aaaa1111", "bbbb1111"} or not per["bbbb1111"].get("vecchia") or per["aaaa1111"].get("vecchia"):
                return f"hc machine ls {cosa}: sessioni {sorted(per)}, attese quella di qui e la vecchia di Studio"
            if d.get("letto") == "prima":
                return f"hc machine ls {cosa}: il documento non è stato riscritto"
        # un elenco vuoto vero: la macchina è stata tolta da Herdr
        d, _ = leggi({"out": json.dumps({"machines": []})})
        if [m["host"] for m in d["macchine"]] != ["qui"] or [x["id"] for x in d["sessioni"]] != ["aaaa1111"]:
            return f"una macchina tolta da Herdr resta nell'elenco: {d['macchine']}"
        # senza hc non c'è Herdr: nessuna macchina oltre a questa, e nessun errore
        d, _ = leggi({}, hc=str(casa / "non-esiste" / "hc"))
        if [m["host"] for m in d["macchine"]] != ["qui"]:
            return f"senza hc l'elenco tiene altre macchine: {d['macchine']}"
        # la nascita su un'altra macchina dice che è Herdr a non rispondere
        cartella = casa / "nascita"
        cartella.mkdir()
        env, _log, _ = lotto4(cartella, dict(studio, ls={"rc": 1, "out": "core non raggiungibile"}))
        r = subprocess.run([sys.executable, str(sonda), "nasci", "Studio", "--", "ciao"], capture_output=True, text=True, timeout=30, env=env)
        try:
            errore = json.loads(r.stdout.strip().splitlines()[-1]).get("errore", "")
        except (ValueError, IndexError):
            errore = ""
        if "Herdr" not in errore or "non è fra le macchine" in errore:
            return f"nasci con Herdr che non risponde: {(r.stdout + r.stderr).strip()[-160:]}"
    except RuntimeError as e:
        return str(e)
    return None


def hz71(repo: Path, casa: Path) -> str | None:
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    m = importlib_spec("volta_sonda_hz71", sonda)
    for testo, atteso in (('[{"a": 1}]', [{"a": 1}]), ('Warning: [beta] nuova versione\n[{"a": 1}]\n', [{"a": 1}]), ("[]", []),
                          ('avviso\n[{"a": 1}]\ncoda [x]', [{"a": 1}]), ("niente [qui]", None), ("", None), ("[1, 2]\n", None)):
        if m.elenco(testo) != atteso:
            return f"elenco({testo!r}) dà {m.elenco(testo)!r}, atteso {atteso!r}"
    for nome in ("SONDA", "NASCI"):
        if "#ELENCO#" in getattr(m, nome) or "def elenco(testo):" not in getattr(m, nome):
            return f"{nome} non porta dentro elenco()"
        try:
            compile(getattr(m, nome), nome, "exec")
        except SyntaxError as e:
            return f"{nome} non è Python valido: {e}"
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    # startedAt di adesso: la sonda lascia fuori le sessioni chiuse nate da più di tre giorni
    sessione = lambda sid, **k: dict({"id": sid[:8], "sessionId": sid, "kind": "background", "state": "done", "cwd": "/p", "startedAt": time.time() * 1000}, **k)  # noqa: E731
    prima = {"letto": "prima", "macchine": [{"macchina": "Questa", "host": "qui", "questa": True}],
             "sessioni": [{"host": "qui", "id": "vvvv0000", "sessionId": "vvvv0000-q"}]}
    sporca = "Warning: [beta] nuova versione\n" + json.dumps([sessione("dddd1111-n")])
    conf = {"macchine": [{"name": "Nuda", "target": "nuda", "state": "connected"}, {"name": "Guasta", "target": "guasta", "state": "connected"}],
            "exec": {"Nuda": {"claude": {"out": sporca}},
                     "Guasta": {"python3": {"out": json.dumps({"errore": "claude agents: boom"})}}}}

    def leggi(modo):
        cartella = casa / f"giro{len(list(casa.glob('giro*')))}"
        cartella.mkdir()
        env, _log, uscita = lotto4(cartella, conf)
        uscita.write_text(json.dumps(dict(prima, macchine=prima["macchine"] + [{"host": "Guasta"}],
                                         sessioni=prima["sessioni"] + [{"host": "Guasta", "id": "gggg0000", "sessionId": "gggg0000-g"}])), encoding="utf-8")
        env.update(HZ_AGENTI=modo, HZ_SESSIONI=json.dumps([sessione("aaaa1111-q")]))
        r = subprocess.run([sys.executable, str(sonda), "volta", "--scrivi", str(uscita)], capture_output=True, text=True, timeout=40, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"volta_sonda.py esce {r.returncode} ({modo}): {(r.stderr or r.stdout).strip()[-160:]}")
        d = json.loads(uscita.read_text(encoding="utf-8"))
        return {x["host"]: x for x in d["macchine"]}, {x["id"]: x for x in d["sessioni"]}

    try:
        # un avviso prima del JSON: le sessioni ci sono, qui e sulla macchina senza Python
        macchine, per = leggi("avviso")
        if "irraggiungibile" in macchine.get("qui", {}) or "aaaa1111" not in per or per["aaaa1111"].get("vecchia"):
            return f"un avviso prima del JSON di claude agents: qui {macchine.get('qui')}, sessioni {sorted(per)}"
        if "irraggiungibile" in macchine.get("Nuda", {"irraggiungibile": 1}) or "dddd1111" not in per:
            return f"un avviso prima del JSON sulla macchina senza Python: {macchine.get('Nuda')}, sessioni {sorted(per)}"
        # la sonda di un'altra macchina dice errore: irraggiungibile col motivo, e le righe di prima
        if macchine.get("Guasta", {}).get("irraggiungibile") != "claude agents: boom" or not per.get("gggg0000", {}).get("vecchia"):
            return f"una sonda che risponde errore: {macchine.get('Guasta')}, sessioni {sorted(per)}"
        # claude agents esce male o non dà un elenco: la macchina è irraggiungibile, non vuota
        for modo, parola in (("rotto", "boom"), ("sporco", "senza elenco")):
            macchine, per = leggi(modo)
            motivo = str(macchine.get("qui", {}).get("irraggiungibile"))
            if parola not in motivo:
                return f"claude agents {modo}: questa macchina non è irraggiungibile col motivo ({macchine.get('qui')})"
            if not per.get("vvvv0000", {}).get("vecchia"):
                return f"claude agents {modo}: le righe dell'ultima lettura spariscono ({sorted(per)})"
        # la nascita: il sessionId intero anche con l'avviso, e anche se la sessione arriva in elenco dopo
        for modo in ("avviso", "tardi"):
            cartella = casa / f"nasce-{modo}"
            cartella.mkdir()
            env, _log, _ = lotto4(cartella, {"macchine": []})
            env.update(HZ_AGENTI=modo, HZ_SESSIONI=json.dumps([sessione("abcd1234-intero", id="abcd1234")]), HZ_CONTA=str(cartella / "conta"))
            r = subprocess.run([sys.executable, str(sonda), "nasci", "qui", "--progetto", "due-mondi", "--", "ciao"],
                               capture_output=True, text=True, timeout=60, env=env)
            try:
                d = json.loads(r.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                return f"nasci ({modo}): uscita senza esito: {(r.stdout + r.stderr).strip()[-160:]}"
            if d.get("sessionId") != "abcd1234-intero":
                return f"nasci ({modo}) non legge il sessionId intero: {d}"
            scheda = cartella / "conf/cache/scheda/abcd1234-intero.json"
            if not scheda.exists() or json.loads(scheda.read_text(encoding="utf-8")).get("progetto") != "due-mondi":
                return f"nasci ({modo}) non scrive il progetto della sessione nata"
    except RuntimeError as e:
        return str(e)
    return None


def hz72(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    env, _log, _ = lotto4(casa, {"macchine": []})
    sid = "aaaa1111-trascritta"
    env.update(HZ_SESSIONI=json.dumps([{"id": "aaaa1111", "sessionId": sid, "kind": "background", "state": "idle", "cwd": "/p"}]))
    progetto = casa / "conf/projects/-p"
    progetto.mkdir(parents=True)
    parla = lambda testo: json.dumps({"type": "assistant", "timestamp": "2026-11-11T10:00:00Z", "message": {"content": [{"type": "text", "text": testo}]}})  # noqa: E731
    righe = ['{"type": "prima riga, che la sonda salta"}', parla("prima"), "5", '"una stringa"', "[1, 2]", "null",
             json.dumps({"type": "assistant", "message": "un messaggio che non è un oggetto"}),
             json.dumps({"type": "assistant", "message": {"content": "testo nudo"}}), parla("ultime parole")]
    (progetto / f"{sid}.jsonl").write_text("\n".join(righe) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(sonda), "volta"], capture_output=True, text=True, timeout=40, env=env)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return f"volta_sonda.py volta: uscita senza elenco: {(r.stdout + r.stderr).strip()[-160:]}"
    qui = next((m for m in d["macchine"] if m["host"] == "qui"), {})
    if "irraggiungibile" in qui:
        return f"una riga della trascrizione che non è un oggetto ferma la sonda: {qui['irraggiungibile'][-120:]}"
    riga = next((x for x in d["sessioni"] if x["sessionId"] == sid), None)
    if not riga or riga.get("risposta") != "ultime parole" or riga.get("ultimo") != "2026-11-11T10:00:00Z":
        return f"le ultime parole dopo le righe storte non si leggono: {riga}"
    return None


PROVA_ESITO = r"""
import { esito, prepara, cambiaSessione, azioneSessione, nuova } from "./dati.mjs";
import { avvisi } from "./herdr.mjs";
const s = { id: "ffff1111", sessionId: "ffff1111-aaaa", host: "qui", macchina: "Questa" };
const caso = process.env.HZ_CASO;
let d = null;
if (caso === "puro") d = JSON.parse(process.env.HZ_RISPOSTE).map((r) => esito(r));
else if (caso === "prepara") d = await prepara(s);
else if (caso === "cambia") d = await cambiaSessione(s, "nome", "Nome mio");
else if (caso === "azione") d = await azioneSessione(s, "stop");
else if (caso === "nasce") d = await nuova("ciao Volta");
console.log(JSON.stringify({ d: d ?? null, avvisi }));
"""


def hz73(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    mod = repo / "shared/volta/mods/arturo"
    dati = (mod / "dati.js").read_text(encoding="utf-8")
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    vecchia = '.split("\\n").pop() || "{}"'
    if vecchia in dati:
        return "dati.js legge ancora un esito senza guardare il codice d'uscita"
    if 'portata = esito(await exec(this.py, [this.sposta, "porta-volta", s.host, s.sessionId], { timeout: 60000 }));' not in volta:
        return "volta.js (porta-volta) non legge l'esito con esito()"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, dati)
    (m / "prova.mjs").write_text(PROVA_ESITO, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")

    def gira(caso, **extra):
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso,
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": [], "arturo.dove": "qui"}), "HZ_HERDR": "{}", **extra}
        for k in ("HZ_NASCE", "HZ_STATO", "HZ_PRONTA", "HZ_HC_ROTTO", "HZ_HC_READ", "HZ_HC_GET", "HZ_EXEC", "HZ_EXEC_CODICE", "HZ_EXEC_ERR", "HZ_RISPOSTE"):
            if k not in extra:
                e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    caduto = "Traceback (most recent call last):\n  File \"x.py\", line 1\nValueError: nessun JSON nell'uscita\n"
    tabella = [
        ({"code": 0, "stdout": '{"ok": true}\n', "stderr": ""}, {"ok": True}),
        ({"code": 0, "stdout": 'avviso della shell\n{"ok": true, "n": 2}\n', "stderr": ""}, {"ok": True, "n": 2}),
        ({"code": 0, "stdout": '{"ok": true}\nuna riga dopo\n', "stderr": ""}, {"ok": True}),
        ({"code": 1, "stdout": '{"errore": "non parte"}\n', "stderr": "rumore"}, {"errore": "non parte"}),
        ({"code": 1, "stdout": '{"ok": true}\n', "stderr": "è caduto dopo"}, {"errore": "è caduto dopo"}),
        ({"code": 0, "stdout": "", "stderr": ""}, {"errore": "nessuna risposta"}),
        ({"code": 0, "stdout": "  \n", "stderr": "solo un avviso"}, {"errore": "solo un avviso"}),
        ({"code": 3, "stdout": "", "stderr": ""}, {"errore": "uscita 3"}),
        ({"code": 1, "stdout": "", "stderr": caduto}, {"errore": "ValueError: nessun JSON nell'uscita"}),
        ({"code": 0, "stdout": "{rotta\n", "stderr": ""}, {"errore": "{rotta"}),
        ({"code": 0, "stdout": "[1, 2]\n", "stderr": ""}, {"errore": "[1, 2]"}),
        ({"code": 2, "stdout": "uso: volta_sonda.py azione\n", "stderr": ""}, {"errore": "uso: volta_sonda.py azione"}),
        ({"code": 1, "stdout": "rumore\n", "stderr": "il motivo vero\n"}, {"errore": "il motivo vero"}),
        ({"code": 1, "stdout": '{"ok": true}\n', "stderr": ""}, {"errore": "uscita 1"}),
    ]
    try:
        avuti = gira("puro", HZ_RISPOSTE=json.dumps([r for r, _ in tabella]))["d"]
        for (r, atteso), avuto in zip(tabella, avuti):
            if avuto != atteso:
                return f"esito({r}) dà {avuto}, atteso {atteso}"
        lungo = gira("puro", HZ_RISPOSTE=json.dumps([{"code": 1, "stdout": "", "stderr": "x" * 900}]))["d"][0]
        if len(lungo.get("errore", "")) > 200:
            return "esito() porta sulla riga un errore di 900 caratteri"
        # chi lo usa: uno script che esce male senza dire niente non passa per un sì
        for caso, nome in (("prepara", "prepara"), ("cambia", "cambiaSessione"), ("azione", "azioneSessione")):
            for extra, parola in (({"HZ_EXEC_CODICE": "1", "HZ_EXEC_ERR": "boom"}, "boom"), ({"HZ_EXEC_CODICE": "0"}, "nessuna risposta"),
                                  ({"HZ_EXEC_CODICE": "1", "HZ_EXEC": '{"ok": true}'}, "uscita 1")):
                d = gira(caso, **extra)["d"]
                if not isinstance(d, dict) or parola not in str(d.get("errore")):
                    return f"{nome} con lo script che risponde {extra}: {d}, atteso un errore con {parola!r}"
            d = gira(caso, HZ_EXEC='{"ok": true}')["d"]
            if d != {"ok": True}:
                return f"{nome} con lo script che risponde ok: {d}"
        v = gira("nasce", HZ_EXEC_CODICE="1", HZ_EXEC_ERR="boom")
        if len(v["avvisi"]) != 1 or "boom" not in v["avvisi"][0].get("body", ""):
            return f"una nascita che esce male senza JSON non dice il motivo: {v['avvisi']}"
        v = gira("nasce", HZ_EXEC_CODICE="1", HZ_EXEC='{"id": "ffff1111", "sessionId": "ffff1111-aaaa", "attach": ["claude", "attach", "ffff1111"]}')
        if v["d"] != {"errore": "uscita 1"} and "errore" not in (v["d"] or {}):
            return f"una nascita uscita male passa per nata: {v['d']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    return None

def lotto5(casa: Path, base: str = "ClaudeCode") -> tuple[dict, Path]:
    """L'ambiente dei casi del registro per lavoro: quello del lotto 4, più la base dei progetti di Volta
    (arturo.json) e una casa finta, così il nome della casa è noto."""
    env, _log, _ = lotto4(casa, {"macchine": []})
    (casa / "app").mkdir(exist_ok=True)
    (casa / "app/arturo.json").write_text(json.dumps({"base": str(casa / base)}), encoding="utf-8")
    (casa / "utente").mkdir(exist_ok=True)
    env.update(HOME=str(casa / "utente"), USERPROFILE=str(casa / "utente"))
    env.pop("PROJECTS_BASE", None)
    return env, casa / "conf/cache"


def leggi5(sonda: Path, env: dict, sessioni: list) -> dict:
    """Una lettura dell'elenco con quelle sessioni di claude agents: le righe per id."""
    r = subprocess.run([sys.executable, str(sonda), "volta"], capture_output=True, text=True, timeout=40,
                       env={**env, "HZ_SESSIONI": json.dumps(sessioni)})
    try:
        d = json.loads(r.stdout)
    except ValueError:
        raise RuntimeError(f"volta_sonda.py volta: uscita senza elenco: {(r.stdout + r.stderr).strip()[-160:]}") from None
    qui = next((m for m in d["macchine"] if m["host"] == "qui"), {})
    if "irraggiungibile" in qui:
        raise RuntimeError(f"la sonda di questa macchina cade: {qui['irraggiungibile'][-160:]}")
    return {x["id"]: x for x in d["sessioni"]}


def scheda5(cache: Path, sid: str, progetto: str, fonte: str) -> None:
    (cache / "scheda").mkdir(parents=True, exist_ok=True)
    (cache / "scheda" / f"{sid}.json").write_text(json.dumps({"stato": "lavoro", "progetto": progetto, "fonte": fonte, "quando": 1}), encoding="utf-8")


def fondo5(lavoro: str, sid: str, **k) -> dict:
    # startedAt di adesso: la sonda lascia fuori le sessioni chiuse nate da più di tre giorni
    return dict({"id": lavoro, "sessionId": sid, "kind": "background", "state": "idle", "cwd": "/p", "startedAt": time.time() * 1000}, **k)


def registro5(cache: Path, lavoro: str) -> dict:
    f = cache / "volta-lavori" / f"{lavoro}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def hz74(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    env, cache = lotto5(casa)
    try:
        scheda5(cache, "aaaa1111-uno", "due-mondi", "inizio")
        per = leggi5(sonda, env, [fondo5("aaaa1111", "aaaa1111-uno")])
        if per["aaaa1111"]["progetto"] != "due-mondi":
            return f"il progetto di /inizio non arriva sulla riga: {per['aaaa1111']['progetto']!r}"
        reg = registro5(cache, "aaaa1111")
        if reg.get("progetto") != "due-mondi" or reg.get("fonte") != "inizio" or reg.get("sessionId") != "aaaa1111-uno":
            return f"una fonte forte non scrive il registro del lavoro: {reg}"
        # /clear: stesso lavoro, sessionId nuovo, scheda nuova che riparte dalla cartella
        scheda5(cache, "bbbb2222-due", "ClaudeCode", "cartella")
        per = leggi5(sonda, env, [fondo5("aaaa1111", "bbbb2222-due")])
        if per["aaaa1111"]["progetto"] != "due-mondi":
            return f"dopo /clear il lavoro perde il progetto: {per['aaaa1111']['progetto']!r} (atteso due-mondi)"
        # un altro sessionId senza nessuna scheda (la sessione fermata, la scheda tolta da SessionEnd)
        per = leggi5(sonda, env, [fondo5("aaaa1111", "cccc3333-tre")])
        if per["aaaa1111"]["progetto"] != "due-mondi":
            return f"senza scheda il lavoro perde il progetto del registro: {per['aaaa1111']['progetto']!r}"
        # il testo dopo /inizio non ancora risolto si vede, ma non entra nel registro
        scheda5(cache, "cccc3333-tre", "testo libero", "prompt")
        per = leggi5(sonda, env, [fondo5("aaaa1111", "cccc3333-tre")])
        if per["aaaa1111"]["progetto"] != "testo libero" or registro5(cache, "aaaa1111").get("progetto") != "due-mondi":
            return f"il testo dopo /inizio: riga {per['aaaa1111']['progetto']!r}, registro {registro5(cache, 'aaaa1111').get('progetto')!r} (attesi testo libero e due-mondi)"
        # una fonte forte nuova vale e aggiorna il registro
        scheda5(cache, "cccc3333-tre", "belleville", "inizio")
        scheda5(cache, "dddd4444-q", "ClaudeCode", "cartella")
        per = leggi5(sonda, env, [fondo5("aaaa1111", "cccc3333-tre"), fondo5("dddd4444", "dddd4444-q")])
        if per["aaaa1111"]["progetto"] != "belleville" or registro5(cache, "aaaa1111").get("progetto") != "belleville":
            return f"un /inizio nuovo non aggiorna il registro: riga {per['aaaa1111']['progetto']!r}, registro {registro5(cache, 'aaaa1111')}"
        # un altro lavoro nella stessa cartella non eredita niente
        if per["dddd4444"]["progetto"] is not None:
            return f"un altro lavoro prende un progetto non suo: {per['dddd4444']['progetto']!r}"
    except RuntimeError as e:
        return str(e)
    return None


def hz75(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    env, cache = lotto5(casa, base="Progetti")
    lavori = cache / "volta-lavori"
    lavori.mkdir(parents=True)
    scheda5(cache, "aaaa1111-a", "Progetti", "cartella")       # la base dei progetti di questa macchina
    scheda5(cache, "bbbb2222-b", "utente", "cartella")         # la casa
    scheda5(cache, "cccc3333-c", "volta-celeste", "cartella")  # un repo vero
    scheda5(cache, "dddd4444-d", "ClaudeCode", "cartella")     # la base di un'altra macchina: qui è una cartella come le altre
    scheda5(cache, "eeee5555-e", "due-mondi", "inizio")
    interattiva = {"sessionId": "eeee5555-e", "kind": "interactive", "status": "idle", "pid": os.getpid(), "cwd": "/p"}
    vecchio = time.time() - 20 * 86400

    def voce(nome, dati, eta=None):
        f = lavori / f"{nome}.json"
        f.write_text(json.dumps(dati), encoding="utf-8")
        if eta:
            os.utime(f, (eta, eta))
        return f

    sparito = voce("pid-999999", {"progetto": "x", "fonte": "inizio", "sessionId": "x"})
    scaduto = voce("vecchio11", {"progetto": "x", "fonte": "inizio", "sessionId": "x"}, vecchio)
    fresco = voce("fresco11", {"progetto": "x", "fonte": "volta", "sessionId": "x"})
    elencato = voce("ffff6666", {"progetto": "belleville", "fonte": "inizio", "sessionId": "ffff6666-f"}, vecchio)
    chiuso = voce("gggg7777", {"progetto": "x", "fonte": "inizio", "sessionId": "gggg7777-g"}, vecchio)
    try:
        per = leggi5(sonda, env, [fondo5("aaaa1111", "aaaa1111-a"), fondo5("bbbb2222", "bbbb2222-b"), fondo5("cccc3333", "cccc3333-c"),
                                  fondo5("dddd4444", "dddd4444-d"), interattiva, fondo5("ffff6666", "ffff6666-f"),
                                  fondo5("gggg7777", "gggg7777-g", state="done", startedAt=(time.time() - 10 * 86400) * 1000)])
    except RuntimeError as e:
        return str(e)
    if per["aaaa1111"]["progetto"] is not None:
        return f"la cartella base passa per un progetto: {per['aaaa1111']['progetto']!r} (la base viene da arturo.json di Volta)"
    if per["bbbb2222"]["progetto"] is not None:
        return f"la casa passa per un progetto: {per['bbbb2222']['progetto']!r}"
    if per["cccc3333"]["progetto"] != "volta-celeste" or per["dddd4444"]["progetto"] != "ClaudeCode":
        return f"una cartella che non è la base perde il suo nome: {per['cccc3333']['progetto']!r}, {per['dddd4444']['progetto']!r}"
    if (lavori / "aaaa1111.json").exists():
        return "un lavoro senza progetto né nome lascia una voce nel registro"
    mio = registro5(cache, f"pid-{os.getpid()}")
    if per["eeee5555"]["progetto"] != "due-mondi" or mio.get("progetto") != "due-mondi":
        return f"un'interattiva non ha il registro sul suo pid: riga {per['eeee5555']['progetto']!r}, registro {mio}"
    if per["ffff6666"]["progetto"] != "belleville":
        return f"il registro di un lavoro elencato non vale: {per['ffff6666']['progetto']!r}"
    if "gggg7777" in per:
        return "la sessione chiusa da dieci giorni è in elenco: il caso non prova più la pulizia"
    if sparito.exists():
        return "la voce di un pid che non c'è più resta: un altro processo con quel pid la erediterebbe"
    if scaduto.exists():
        return "la voce di un lavoro non più elencato da 20 giorni resta"
    if not fresco.exists():
        return "la pulizia toglie una voce appena scritta: la nascita la scrive prima che claude agents elenchi la sessione"
    if not elencato.exists():
        return "la pulizia toglie la voce di un lavoro ancora elencato"
    if not chiuso.exists():
        return "la pulizia toglie la voce di un lavoro chiuso da più di tre giorni, che claude agents elenca ancora"
    return None


def hz76(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # il claude finto è uno script con shebang
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    env, cache = lotto5(casa)

    def titolo(sid, testo, fonte, **k):
        (cache / "titolo").mkdir(parents=True, exist_ok=True)
        (cache / "titolo" / f"{sid}.json").write_text(json.dumps(dict({"titolo": testo, "fonte": fonte, "quando": 1, "peso": 0}, **k)), encoding="utf-8")

    # la nascita non legge il sessionId (claude agents non elenca ancora la sessione): il registro c'è lo stesso
    r = subprocess.run([sys.executable, str(sonda), "nasci", "qui", "--progetto", "due-mondi", "--", "ciao"],
                       capture_output=True, text=True, timeout=60, env={**env, "HZ_SESSIONI": "[]"})
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return f"nasci: uscita senza esito: {(r.stdout + r.stderr).strip()[-160:]}"
    if d.get("id") != "abcd1234" or d.get("sessionId") != "abcd1234":
        return f"nasci: il caso vuole una nascita senza sessionId letto: {d}"
    reg = registro5(cache, "abcd1234")
    if reg.get("progetto") != "due-mondi" or reg.get("fonte") != "volta":
        return f"la nascita non scrive subito il registro del lavoro: {reg}"
    try:
        scheda5(cache, "abcd1234-intero", "ClaudeCode", "cartella")
        titolo("abcd1234-intero", "Nome mio", "persona", portato=True)
        titolo("eeee1111-a", "Titolo automatico", "auto")
        per = leggi5(sonda, env, [fondo5("abcd1234", "abcd1234-intero"), fondo5("eeee1111", "eeee1111-a")])
        if per["abcd1234"]["progetto"] != "due-mondi":
            return f"la sessione appena nata non sta sotto il suo progetto: {per['abcd1234']['progetto']!r}"
        if per["abcd1234"]["titolo"] != "Nome mio" or per["eeee1111"]["titolo"] != "Titolo automatico":
            return f"i titoli non si leggono: {per['abcd1234']['titolo']!r}, {per['eeee1111']['titolo']!r}"
        # /clear dei due lavori: il nome della persona resta, il titolo automatico no
        dopo = [fondo5("abcd1234", "ffff2222-dopo"), fondo5("eeee1111", "eeee2222-b")]
        for giro in ("subito dopo /clear", "alla lettura seguente"):
            per = leggi5(sonda, env, dopo)
            if per["abcd1234"]["titolo"] != "Nome mio":
                return f"{giro} il lavoro perde il nome dato dalla persona: {per['abcd1234']['titolo']!r}"
            if per["abcd1234"]["daPortare"] is not None:
                return f"{giro} il nome ereditato chiede un altro /rename: {per['abcd1234']['daPortare']!r}"
            if per["eeee1111"]["titolo"] is not None:
                return f"{giro} un titolo automatico passa al sessionId nuovo: {per['eeee1111']['titolo']!r}"
        f = cache / "titolo/ffff2222-dopo.json"
        scritto = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        if scritto.get("fonte") != "persona" or scritto.get("titolo") != "Nome mio" or scritto.get("portato") is not True:
            return f"il nome non passa al file del sessionId nuovo: {scritto}"
        # la persona toglie il nome dalla finestra: non torna, nemmeno al /clear seguente
        r = subprocess.run([sys.executable, str(sonda), "rinomina", "qui", "ffff2222-dopo"], capture_output=True, text=True, timeout=40, env=env)
        if r.returncode != 0:
            return f"Rinomina vuoto esce {r.returncode}: {(r.stdout + r.stderr).strip()[-160:]}"
        per = leggi5(sonda, env, dopo)
        if per["abcd1234"]["titolo"] is not None or "titolo" in registro5(cache, "abcd1234"):
            return f"un nome tolto dalla persona resta: riga {per['abcd1234']['titolo']!r}, registro {registro5(cache, 'abcd1234')}"
        per = leggi5(sonda, env, [fondo5("abcd1234", "gggg3333-poi")])
        if per["abcd1234"]["titolo"] is not None:
            return f"un nome tolto dalla persona torna al /clear seguente: {per['abcd1234']['titolo']!r}"
        if per["abcd1234"]["progetto"] != "due-mondi":
            return f"dopo due /clear il lavoro perde il progetto: {per['abcd1234']['progetto']!r}"
    except RuntimeError as e:
        return str(e)
    return None



PROVA_ALTROVE = r"""
import { altrove, stacca, apriSessione } from "./dati.mjs";
import { lanciati } from "./herdr.mjs";
const s = { id: "ffff1111", sessionId: "ffff1111-aaaa", host: "qui", macchina: "Questa", questa: true, nome: "Progetto x",
            progetto: "progetto-x", stato: "ferma", tipo: "background" };
const prima = altrove(s).map((x) => x.address);
let staccati = null, dopo = null, esito = null;
if (process.env.HZ_CASO === "stacca") {
  staccati = stacca(s);
  dopo = altrove(s).map((x) => x.address);
  const r = await apriSessione(s, ["claude", "attach", "ffff1111"], true);
  esito = { ...r, veglia: undefined };
}
console.log(JSON.stringify({ prima, staccati, dopo, esito, lanciati, senza: altrove(null), vuota: altrove({}) }));
"""


def hz77(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    volta_js = (mod / "volta.js").read_text(encoding="utf-8")
    # il clic: la frase del primo clic si legge prima di toglierla, e l'avviso ferma il clic prima della scheda
    ordine = ("const secondo = this.avvisi[chiave(s)] === ALTROVE;", "delete this.avvisi[chiave(s)];",
              'if (d.azione === "aggancia" && this.fuori(s, secondo, cx)) return;',
              'if (d.azione === "aggancia") return this.apri(s, d.argv, false, cx);')
    posti = [volta_js.find(p) for p in ordine]
    if -1 in posti or posti != sorted(posti):
        return f"volta.js, premi: mancano o sono fuori ordine {[p for p, i in zip(ordine, posti) if i == -1] or ordine}"
    for pezzo in ('const ALTROVE = "È aperta in un Terminale. Un altro clic la porta qui.";',
                  "  fuori(s, secondo, cx) {\n    if (!altrove(s).length) return false;\n    if (secondo) { stacca(s); return false; }\n"
                  "    this.avvisa(s, ALTROVE, cx, ALTROVE_MS);\n    return true;\n  }",
                  "esito, altrove, stacca, schedeAgganciate, congedaSessione } from \"./dati.js\";"):
        if pezzo not in volta_js:
            return f"volta.js senza {pezzo[:70]}"
    node = shutil.which("node")
    if not node:
        return None
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_ALTROVE, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    spazio = {"id": "s1", "name": "progetto-x", "named": True, "active": True, "tabs": [{"id": "tb0", "name": "Shell"}, {"id": "tb1", "name": "Altro"}]}
    shell = {"address": "t3", "argv": ["zsh"], "state": "live"}
    # come lo lascia il lanciatore volta-claude in una finestra del Terminale: nessun pannello lo mostra
    fuori = {"address": "t9", "argv": ["sh", "-c", "claude attach ffff1111"], "state": "live", "labels": {}}
    scheda = {"address": "t7", "argv": ["/bin/zsh", "-lic", '"$@"; exec "$0" -li', "/bin/zsh", "claude", "attach", "ffff1111"], "state": "live"}

    def volta(terminali, pannelli=("t3",), caso="guarda", **extra):
        herdr = {"spaces": [spazio], "terminals": terminali, "panes": [{"terminal": x, "tab": "tb0" if x == "t3" else "tb1"} for x in pannelli]}
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso, "HZ_EXEC": '{"ok": true}',
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": [], "arturo.dove": "qui"}), "HZ_HERDR": json.dumps(herdr), **extra}
        for k in ("HZ_NASCE", "HZ_STATO", "HZ_PRONTA", "HZ_HC_ROTTO", "HZ_HC_READ", "HZ_HC_GET", "HZ_CHIUDE", "HZ_EXEC_CODICE", "HZ_EXEC_ERR"):
            if k not in extra:
                e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    try:
        # il caso vero: la finestra del Terminale aggancia la sessione, nella finestra di Volta non c'è scheda
        v = volta([shell, fuori])
        if v["prima"] != ["t9"] or v["senza"] != [] or v["vuota"] != []:
            return f"un terminale che aggancia la sessione fuori dai pannelli non si trova: {v['prima']}, senza sessione {v['senza']}, {v['vuota']}"
        # per etichetta, quando l'argv non dice niente
        v = volta([shell, {"address": "t9", "argv": ["zsh"], "state": "live", "labels": {"arturo.sessione": "ffff1111"}}])
        if v["prima"] != ["t9"]:
            return f"un terminale con l'etichetta della sessione, fuori dai pannelli, non si trova: {v['prima']}"
        # la sessione ha una scheda nella finestra: il clic porta davanti quella, niente da staccare
        v = volta([shell, scheda, fuori], pannelli=("t3", "t7"))
        if v["prima"] != []:
            return f"con una scheda della sessione nella finestra risulta ancora aperta altrove: {v['prima']}"
        # chiuso, di un'altra macchina, di un'altra sessione, senza argv: non contano
        for cosa, x in (("un terminale già chiuso", {**fuori, "state": "exited"}),
                        ("un terminale di un'altra macchina", {**fuori, "address": "amaltea/t9"}),
                        ("un terminale di un'altra sessione", {**fuori, "argv": ["sh", "-c", "claude attach aaaa2222"]}),
                        ("un terminale con l'etichetta di un'altra sessione", {"address": "t9", "argv": ["zsh"], "state": "live", "labels": {"arturo.sessione": "aaaa2222"}}),
                        ("un terminale senza argv", {"address": "t9", "state": "live"})):
            v = volta([shell, x])
            if v["prima"] != []:
                return f"{cosa} passa per un aggancio della sessione: {v['prima']}"
        # senza stato (un Herdr che non lo dice) vale come vivo
        v = volta([shell, {"address": "t9", "argv": fuori["argv"]}])
        if v["prima"] != ["t9"]:
            return f"un terminale senza stato non si trova: {v['prima']}"
        # il secondo clic: i terminali fuori si chiudono, poi nasce la scheda; la sessione non si ferma
        v = volta([shell, fuori, {**fuori, "address": "t10"}], caso="stacca", HZ_CHIUDE="1", HZ_NASCE="t11", HZ_HC_GET=json.dumps({"t11": [{"state": "live", "pid": 10, "argv": ["x"], "foreground": {"pid": 77, "argv": ["claude"]}}]}))
        if v["prima"] != ["t9", "t10"] or v["staccati"] != 2 or v["dopo"] != []:
            return f"stacca non chiude i terminali fuori dalla finestra: prima {v['prima']}, staccati {v['staccati']}, dopo {v['dopo']}"
        cmd = [x["cmd"] for x in v["lanciati"] if x["cmd"] in ("terminal.kill", "tab.new", "space.new", "tab.close")]
        if cmd != ["terminal.kill", "terminal.kill", "tab.new"] or [x.get("terminal") for x in v["lanciati"] if x["cmd"] == "terminal.kill"] != ["t9", "t10"]:
            return f"dopo lo stacco non nasce una scheda sola, o si chiude altro: {v['lanciati']}"
        if v["esito"].get("come") != "nuova" or any(x[:1] == ["stop"] for x in v.get("eseguiti", [])):
            return f"dopo lo stacco la sessione non si apre in una scheda nuova: {v['esito']}"
        # con la scheda nella finestra stacca non tocca niente
        v = volta([shell, scheda, fuori], pannelli=("t3", "t7"), caso="stacca", HZ_HC_GET=json.dumps({"t7": [{"state": "live", "pid": 10, "argv": scheda["argv"], "foreground": {"pid": 77, "argv": ["claude"]}}]}))
        if v["staccati"] != 0 or any(x["cmd"] == "terminal.kill" for x in v["lanciati"]) or v["esito"].get("come") != "davanti":
            return f"con la scheda nella finestra stacca chiude qualcosa: {v['staccati']}, {v['lanciati']}, {v['esito']}"
    except (RuntimeError, ValueError, KeyError) as e:
        return f"dati.js non gira con node: {e}"
    return None


class Mic7:
    """L'ambiente dei casi del microfono del lotto 7: audio finto, cache, comandi di volta_microfono.py."""
    MIC, BH, ALTRO = "mic-vero", "BlackHole2ch_UID", "cuffie"

    def __init__(self, repo: Path, casa: Path):
        self.script = repo / "shared/volta/mods/arturo/volta_microfono.py"
        self.cache, self.audio = casa / "mic-cache", casa / "audio.json"
        self.ingressi = [{"uid": self.MIC, "nome": "Microfono"}, {"uid": self.BH, "nome": "BlackHole 2ch"}, {"uid": self.ALTRO, "nome": "Cuffie"}]
        self.beve = [sys.executable, "-c", "import sys\nwhile sys.stdin.buffer.read(4096): pass"]
        self.base = {k: v for k, v in os.environ.items() if not k.startswith("VOLTA_")}
        self.figli = []

    def amb(self, **altro):
        return {**self.base, "VOLTA_CACHE": str(self.cache), "VOLTA_MIC_AUDIO": str(self.audio), "VOLTA_MIC_SUONA": json.dumps(self.beve), **altro}

    def senza(self, *uid):
        return [x for x in self.ingressi if x["uid"] not in uid]

    def suono(self, uid, lista=None):
        self.audio.write_text(json.dumps({"predefinito": uid, "ingressi": self.ingressi if lista is None else lista}), encoding="utf-8")

    def metti(self, uid, lista=None, stato=None):
        """Audio da capo, cache vuota; con `stato` anche il microfono.json di un ponte di prima."""
        shutil.rmtree(self.cache, ignore_errors=True)
        self.suono(uid, lista)
        if stato is not None:
            self.cache.mkdir(parents=True, exist_ok=True)
            (self.cache / "microfono.json").write_text(json.dumps(stato), encoding="utf-8")

    def ingresso(self):
        return json.loads(self.audio.read_text(encoding="utf-8"))["predefinito"]

    def salvato(self):
        f = self.cache / "microfono.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    def ricevi(self, entrata=subprocess.PIPE, **altro):
        p = subprocess.Popen([sys.executable, str(self.script), "ricevi"], stdin=entrata, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=self.amb(**altro))
        self.figli.append(p)
        return p, json.loads(p.stdout.readline().decode("utf-8") or "{}")

    def fine(self, p, attesa=10):
        try:
            return p.wait(timeout=attesa)
        except subprocess.TimeoutExpired:
            p.kill()
            return None

    def comando(self, *argv, **altro):
        r = subprocess.run([sys.executable, str(self.script), *argv], capture_output=True, text=True, encoding="utf-8",
                           stdin=subprocess.DEVNULL, timeout=30, env=self.amb(**altro))
        try:
            return json.loads((r.stdout or "").strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {"rc": r.returncode, "uscita": (r.stdout + r.stderr)[:200]}

    def processo(self, *coda):
        """Un processo vivo che dorme: `coda` sono le parole in fondo alla sua riga di comando."""
        p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)", *coda])
        self.figli.append(p)
        return p

    def aspetta(self, cosa, secondi=8):
        fino = time.time() + secondi
        while time.time() < fino:
            if cosa():
                return True
            time.sleep(0.2)
        return False

    def chiudi(self):
        for p in self.figli:
            if p.poll() is None:
                p.kill()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass


def hz78(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # il ponte del microfono c'è solo sul Mac
    m = Mic7(repo, casa)
    MIC, BH, ALTRO = m.MIC, m.BH, m.ALTRO
    morto = subprocess.Popen([sys.executable, "-c", "pass"])
    morto.wait()
    try:
        # l'ingresso di prima sparisce mentre il ponte è su (cuffie staccate): torna il primo ingresso vero
        m.metti(ALTRO)
        p, riga = m.ricevi()
        if riga.get("esito") != "attivo" or m.ingresso() != BH:
            return f"ricevi non parte: {riga}, ingresso {m.ingresso()}"
        m.suono(BH, m.senza(ALTRO))
        p.stdin.close()
        if m.fine(p) != 0 or m.ingresso() != MIC:
            return f"se l'ingresso di prima è sparito il microfono resta sul virtuale: ingresso {m.ingresso()} (atteso {MIC})"
        # lo stesso con ripara, dopo un ponte morto male
        m.metti(BH, m.senza(ALTRO), {"pid": morto.pid, "prima": ALTRO, "virtuale": BH})
        r = m.comando("ripara")
        if r.get("esito") != "riparato" or r.get("rimesso") is not True or m.ingresso() != MIC or m.salvato() is not None:
            return f"ripara non ripiega su un ingresso vero quando quello di prima è sparito: {r}, ingresso {m.ingresso()}"
        # l'ingresso di prima c'è ancora: torna lui, non il primo dell'elenco
        m.metti(BH, None, {"pid": morto.pid, "prima": ALTRO, "virtuale": BH})
        if m.comando("ripara").get("rimesso") is not True or m.ingresso() != ALTRO:
            return f"ripara non rimette l'ingresso di prima quando c'è ancora: ingresso {m.ingresso()} (atteso {ALTRO})"
        # il virtuale è già l'ingresso e non c'è stato: non si salva come "prima", e a fine flusso torna un ingresso vero
        m.metti(BH)
        p, riga = m.ricevi()
        s = m.salvato() or {}
        if riga.get("esito") != "attivo" or riga.get("prima") != MIC or s.get("prima") != MIC:
            m.fine(p, 0)
            return f"il virtuale si salva come ingresso di prima: riga {riga}, salvato {s.get('prima')!r} (atteso {MIC})"
        p.stdin.close()
        if m.fine(p) != 0 or m.ingresso() != MIC:
            return f"partito dal virtuale, a fine flusso il microfono resta sul virtuale: {m.ingresso()}"
        # lo stesso con un microfono.json rimasto che dice "prima = virtuale"
        m.metti(BH, None, {"pid": morto.pid, "prima": BH, "virtuale": BH})
        if m.comando("ripara").get("rimesso") is not True or m.ingresso() != MIC:
            return f"ripara lascia il virtuale quando il file dice che era l'ingresso di prima: {m.ingresso()}"
        # nessun ingresso vero: non cade e non tocca niente
        m.metti(BH, m.senza(MIC, ALTRO))
        p, riga = m.ricevi()
        p.stdin.close()
        if riga.get("esito") != "attivo" or m.fine(p) != 0 or m.ingresso() != BH or m.salvato() is not None:
            return f"senza un ingresso vero ricevi non chiude pulito: {riga}, ingresso {m.ingresso()}"
        # una scelta fatta a mano resta anche con ripara
        m.metti(ALTRO, None, {"pid": morto.pid, "prima": MIC, "virtuale": BH})
        if m.comando("ripara").get("rimesso") is not False or m.ingresso() != ALTRO:
            return f"ripara cambia un ingresso scelto a mano: {m.ingresso()}"
        # il pid salvato oggi è un altro programma: non è un ponte vivo
        altro = m.processo()
        m.metti(BH, None, {"pid": altro.pid, "prima": MIC, "virtuale": BH})
        st = m.comando("stato")
        if st.get("remoto", {}).get("ponte") is not False:
            return f"stato dà per vivo un ponte il cui pid è di un altro programma: {st}"
        r = m.comando("ripara")
        if r.get("esito") != "riparato" or m.ingresso() != MIC:
            return f"ripara scambia il pid di un altro programma per un ponte vivo: {r}, ingresso {m.ingresso()}"
        m.metti(BH, None, {"pid": altro.pid, "prima": MIC, "virtuale": BH})
        p, riga = m.ricevi()
        p.stdin.close()
        if riga.get("esito") != "attivo" or m.fine(p) != 0 or m.ingresso() != MIC:
            return f"ricevi rifiuta il ponte per un pid che è di un altro programma: {riga}"
        # questo script in un altro ruolo (il ponte locale) non è il ricevitore
        ponte = m.processo("volta_microfono.py", "ponte", "amaltea")
        m.metti(BH, None, {"pid": ponte.pid, "prima": MIC, "virtuale": BH})
        if m.comando("ripara").get("esito") != "riparato":
            return "ripara scambia il ponte locale per un ricevitore vivo"
        # il ricevitore vero resta
        vivo = m.processo("volta_microfono.py", "ricevi")
        m.metti(BH, None, {"pid": vivo.pid, "prima": MIC, "virtuale": BH})
        if m.comando("ripara").get("esito") != "ponte vivo" or m.ingresso() != BH or m.comando("stato").get("remoto", {}).get("ponte") is not True:
            return "un ricevitore vivo non è più riconosciuto"
        # la sonda delle sessioni lancia ripara quando trova microfono.json
        sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
        env, _cache = lotto5(casa)
        (casa / "app/mods/arturo").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(m.script, casa / "app/mods/arturo/volta_microfono.py")
        env = {**env, "VOLTA_CACHE": str(m.cache), "VOLTA_MIC_AUDIO": str(m.audio)}
        m.metti(BH, None, {"pid": morto.pid, "prima": MIC, "virtuale": BH})
        leggi5(sonda, env, [])
        if m.ingresso() != MIC or m.salvato() is not None:
            return f"la sonda non ripara un ponte morto male: ingresso {m.ingresso()}, microfono.json {'resta' if m.salvato() else 'tolto'}"
        m.metti(BH, None, {"pid": vivo.pid, "prima": MIC, "virtuale": BH})
        leggi5(sonda, env, [])
        if m.ingresso() != BH or m.salvato() is None:
            return "la sonda tocca un ponte vivo"
        # senza microfono.json la sonda non lancia niente: un ingresso sul virtuale scelto a mano resta
        m.metti(BH)
        leggi5(sonda, env, [])
        if m.ingresso() != BH:
            return "la sonda cambia l'ingresso anche senza microfono.json"
    except RuntimeError as e:
        return str(e)
    finally:
        m.chiudi()
    return None


def hz79(repo: Path, casa: Path) -> str | None:
    if os.name == "nt":
        return None  # il ponte del microfono c'è solo sul Mac
    import signal  # noqa: PLC0415
    m = Mic7(repo, casa)
    MIC, BH = m.MIC, m.BH
    zeri = [sys.executable, "-c", "import sys, time\nwhile True:\n    sys.stdout.buffer.write(bytes(3200)); sys.stdout.buffer.flush(); time.sleep(0.01)"]
    finti = {"VOLTA_MIC_CATTURA": json.dumps(zeri), "VOLTA_MIC_SSH": json.dumps([sys.executable, str(m.script), "ricevi"])}

    def vivi(pid):
        try:
            os.killpg(pid, 0)
            return True
        except OSError:
            return False
    try:
        # l'uscita audio non legge più: la scrittura ha un tetto, il ricevitore chiude e l'ingresso torna
        m.metti(MIC)
        sorda = [sys.executable, "-c", "import time; time.sleep(120)"]
        fonte = subprocess.Popen(zeri, stdout=subprocess.PIPE)
        m.figli.append(fonte)
        p, riga = m.ricevi(entrata=fonte.stdout, VOLTA_MIC_SUONA=json.dumps(sorda), VOLTA_MIC_SILENZIO="1")
        fonte.stdout.close()
        if riga.get("esito") != "attivo":
            return f"ricevi non parte: {riga}"
        if m.fine(p, 8) != 0 or m.ingresso() != MIC or m.salvato() is not None:
            return f"con un'uscita audio che non legge il ricevitore resta appeso: ingresso {m.ingresso()}"
        fonte.kill()
        # il ponte ucciso (kill -9) lascia cattura e ssh: spegni chiude il gruppo e l'ingresso torna
        m.metti(MIC)
        m.comando("accendi", "amaltea", **finti)
        if not m.aspetta(lambda: m.comando("stato", **finti).get("locale", {}).get("stato") == "attivo" and m.ingresso() == BH):
            return f"il ponte locale non arriva ad attivo: {m.comando('stato', **finti)}"
        pid = json.loads((m.cache / "microfono-locale.json").read_text(encoding="utf-8"))["pid"]
        os.kill(pid, signal.SIGKILL)
        if not m.aspetta(lambda: m.comando("stato", **finti).get("locale", {}).get("stato") == "errore", 5):
            return f"un ponte ucciso non risulta chiuso: {m.comando('stato', **finti)}"
        if not vivi(pid) or m.ingresso() != BH:
            return "il caso non regge: ucciso il ponte, cattura e ssh dovevano restare"
        if m.comando("spegni", **finti).get("stato") != "spento" or not m.aspetta(lambda: not vivi(pid) and m.ingresso() == MIC, 6):
            return f"spegni lascia vivi cattura e ssh di un ponte ucciso: gruppo {'vivo' if vivi(pid) else 'chiuso'}, ingresso {m.ingresso()}"
        # lo stesso quando chi riaccende è `accendi`: prima chiude il gruppo di prima
        m.metti(MIC)
        m.comando("accendi", "amaltea", **finti)
        if not m.aspetta(lambda: m.comando("stato", **finti).get("locale", {}).get("stato") == "attivo"):
            return "il secondo ponte non parte"
        pid = json.loads((m.cache / "microfono-locale.json").read_text(encoding="utf-8"))["pid"]
        os.kill(pid, signal.SIGKILL)
        m.aspetta(lambda: m.comando("stato", **finti).get("locale", {}).get("stato") == "errore", 5)
        m.comando("accendi", "amaltea", **finti)
        if not m.aspetta(lambda: not vivi(pid), 6):
            return "accendi apre un ponte nuovo senza chiudere cattura e ssh di quello ucciso"
        if not m.aspetta(lambda: m.comando("stato", **finti).get("locale", {}).get("stato") == "attivo" and m.ingresso() == BH):
            return f"dopo un ponte ucciso accendi non riparte: {m.comando('stato', **finti)}"
        m.comando("spegni", **finti)
        if not m.aspetta(lambda: m.ingresso() == MIC):
            return "spegni non chiude il ponte ripartito"
        # il pid salvato oggi è un altro programma, capo di un gruppo suo: spegni non lo tocca
        altro = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], start_new_session=True)
        m.figli.append(altro)
        m.metti(MIC)
        m.cache.mkdir(parents=True, exist_ok=True)
        (m.cache / "microfono-locale.json").write_text(json.dumps({"pid": altro.pid, "target": "amaltea", "stato": "attivo"}), encoding="utf-8")
        st = m.comando("stato", **finti).get("locale", {})
        if st.get("stato") != "errore":
            return f"stato dà per vivo un ponte il cui pid è di un altro programma: {st}"
        m.comando("spegni", **finti)
        time.sleep(0.5)
        if altro.poll() is not None:
            return "spegni chiude un programma che non è il ponte"
        if (m.cache / "microfono-locale.json").exists():
            return "spegni lascia il file di un ponte che non c'è più"
    finally:
        m.comando("spegni", **finti)
        m.chiudi()
    return None


PROVA_BERSAGLIO = """
import { bersaglio } from %s;
const s = (id, attach) => ({ id, questa: false, macchina: "M", attach });
const sessioni = [s("aaaa1111", ["ssh", "-t", "amaltea", "/Users/u/.local/bin/claude", "attach", "aaaa1111"]),
  s("bbbb2222", ["ssh", "-t", "torre", "C:\\\\Users\\\\feder\\\\.local\\\\bin\\\\claude.EXE", "attach", "bbbb2222"]),
  s("cccc3333", ["ssh", "-t", "torre", "claude.exe", "attach", "cccc3333"]),
  s("dddd4444", ["ssh", "-t", "torre", "D:/strumenti/claude", "attach", "dddd4444"]),
  s("eeee5555", ["C:\\\\Windows\\\\System32\\\\OpenSSH\\\\ssh.exe", "-t", "amaltea", "/Users/u/.local/bin/claude", "attach", "eeee5555"]),
  s("ffff6666", ["ssh", "-t", "amaltea", "claude", "attach", "ffff6666"]),
  s("gggg7777", ["ssh", "-t", "linux", "/home/c/exe/claude", "attach", "gggg7777"]),
  s("hhhh8888", ["ssh", "-t", "torre", "claude.EXE", "attach", "hhhh8888"])];
const b = (id) => bersaglio({ address: "t5", argv: ["x"], labels: { "arturo.sessione": id } }, sessioni)?.target ?? null;
console.log(JSON.stringify({ mac: b("aaaa1111"), win: b("bbbb2222"), exe: b("cccc3333"), disco: b("dddd4444"), daWindows: b("eeee5555"), nudo: b("ffff6666"), linux: b("gggg7777"), maiuscolo: b("hhhh8888") }));
"""

PROVA_PERCHE = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("vm", sys.argv[1])
vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vm)
print(json.dumps([vm.perche(x) for x in json.loads(sys.argv[2])]))
"""


def hz80(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    errori = ["persona@amaltea: Permission denied (publickey,password,keyboard-interactive).",
              "Host key verification failed.",
              "[avfoundation @ 0x1] Failed to create AV capture input device: not authorized",
              "ssh: connect to host amaltea port 22: Operation timed out",
              "ssh: Could not resolve hostname amaltea: nodename nor servname provided",
              "qualcosa\nultima riga", ""]
    r = subprocess.run([sys.executable, "-c", PROVA_PERCHE, str(mod / "volta_microfono.py"), json.dumps(errori)],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    if r.returncode != 0:
        return f"volta_microfono.py non si importa: {(r.stderr or r.stdout).strip()[-200:]}"
    frasi = json.loads(r.stdout.strip().splitlines()[-1])
    chiave = "l'altra macchina non accetta la chiave ssh di questa"
    attese = [chiave, chiave, "permesso microfono negato", "l'altra macchina non risponde", "l'altra macchina non risponde",
              "ultima riga", "il ponte si è chiuso"]
    if frasi != attese:
        diverso = next((e, a, f) for e, a, f in zip(errori, attese, frasi) if a != f)
        return f"perche({diverso[0][:60]!r}): attesa {diverso[1]!r}, avuta {diverso[2]!r}"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "microfono.mjs"
    shutil.copyfile(mod / "microfono.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_BERSAGLIO % json.dumps(copia.as_uri())],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    if r.returncode != 0:
        return f"microfono.js non gira: {(r.stderr or r.stdout).strip()[:200]}"
    v = json.loads(r.stdout.strip().splitlines()[-1])
    atteso = {"mac": "amaltea", "win": None, "exe": None, "disco": None, "daWindows": "amaltea", "nudo": "amaltea", "linux": "linux", "maiuscolo": None}
    if v != atteso:
        return f"bersaglio verso una macchina Windows: atteso {atteso}, avuto {v}"
    return None


def hz81(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta"
    mod = vc / "mods/arturo"
    bj = (mod / "barra.js").read_text(encoding="utf-8")
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for testo, pezzo, guasto in (
        (bj, 'return v_flex().size_full().overflow_hidden().bg(t.chrome)\n', "la radice della barra non taglia quello che non entra"),
        (bj, '.child(v_flex().id("barra-cima").flex_none()', "la cima della barra non ha un id per misurarsi"),
        (bj, 'if (shared("arturo.misura.cima")?.altezza !== v.altezza) setShared("arturo.misura.cima", v);', "la cima della barra non scrive la sua misura"),
        (vj, '.id("volta-gesti").max_h(GESTI_MAX).flex_none().overflow_y_scroll()', "il riquadro dei gesti non ha un tetto con lo scorrimento"),
    ):
        if testo.count(pezzo) != 1:
            return guasto
    lay = json.loads((vc / "layouts/arturo.json").read_text(encoding="utf-8"))
    barra = next((n for n in lay.get("children", []) if n.get("id") == "sidebar"), None)
    if not barra or barra.get("resizable") is not False:
        return "layout arturo: il divisore sopra il piede si trascina ancora (sidebar senza resizable false)"
    if lay.get("resizable") is False:
        return "layout arturo: la colonna di sinistra non si allarga più (resizable false sulla radice)"
    piede = next((n for n in barra.get("children", []) if n.get("id") == "piede"), {})
    if (piede.get("size") or {}).get("px") != piede_misure(repo):
        return f"layout arturo: il piede è alto {(piede.get('size') or {}).get('px')}, atteso PIEDE di misure.js (una misura diversa da quella salvata fa cadere il trascinamento)"
    return None


TOLTI = ["mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato"]
PROVA_TASTI = """
import json, sys
sys.path.insert(0, sys.argv[1])
import volta_mod
from pathlib import Path
print(json.dumps({"quanti": volta_mod.tasti(Path(sys.argv[1])), "elenco": list(volta_mod.TASTI_VECCHI)}))
"""


def hz82(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta"
    # 1. l'installazione
    app = casa / "app"
    app.mkdir(parents=True)
    prima = {"cmd-o": TOLTI[0], "cmd-shift-n": TOLTI[1], "cmd-shift-e": TOLTI[2], "cmd-t": "pane.split:right",
             "cmd-shift-down": "mod.open:arturo-stato-mio", "f5": TOLTI[0]}
    (app / "keys.json").write_text(json.dumps({"global": prima}), encoding="utf-8")
    r = installa(repo, casa)
    if r.returncode != 0:
        return f"installazione fallita: {(r.stdout + r.stderr)[-200:]}"
    avuti = leggi(app / "keys.json")["global"]
    attesi = {"cmd-o": "arturo.apri", "cmd-shift-n": "arturo.nota", "cmd-shift-e": "arturo.note", "cmd-t": "pane.split:right",
              "cmd-shift-down": "mod.open:arturo-stato-mio", "f5": TOLTI[0]}
    for k, v in attesi.items():
        if avuti.get(k) != v:
            return f"installa-herdr.sh: {k} era {prima[k]}, ora {avuti.get(k)}, atteso {v}"
    if "tasto cmd-o lasciato" in r.stdout or "tasto cmd-shift-down lasciato com'era" not in r.stdout:
        return f"installa-herdr.sh dice il falso sui tasti lasciati: {r.stdout[-300:]}"
    testo = (vc / "installa-herdr.sh").read_text(encoding="utf-8")
    m = re.search(r"^VECCHI = \((.*)\)$", testo, re.M)
    if not m or sorted(json.loads("[" + m.group(1) + "]")) != sorted(TOLTI):
        return "installa-herdr.sh: l'elenco dei mod tolti non è quello dei tre mod"
    # 2. l'aggiornamento del mod: tasti() di volta_mod.py sulla fonte vera
    nome = "keys.json" if sys.platform == "darwin" else "keys-ctrl.json"
    fonte = list(leggi(vc / nome)["global"].items())
    if len(fonte) < 4:
        return f"{nome} ha meno di quattro tasti"
    app2 = casa / "app2"
    app2.mkdir()
    miei = {fonte[i][0]: TOLTI[i] for i in range(3)}
    miei.update({fonte[3][0]: "mod.open:arturo-stato-mio", "f5": TOLTI[0]})
    (app2 / "keys.json").write_text(json.dumps({"global": miei, "terminal": {fonte[0][0]: TOLTI[0]}}), encoding="utf-8")
    r = subprocess.run([sys.executable, "-c", PROVA_TASTI, str(vc)], capture_output=True, text=True, timeout=30,
                       env={**os.environ, "HERDR_APP_HOME": str(app2)})
    if r.returncode != 0:
        return f"tasti() di volta_mod.py non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if sorted(d["elenco"]) != sorted(TOLTI):
        return f"volta_mod.py: l'elenco dei mod tolti è {d['elenco']}"
    dopo = leggi(app2 / "keys.json")
    attesi2 = dict(miei, **{fonte[i][0]: fonte[i][1] for i in range(3)})
    # i due tasti del giro fra le sessioni (HZ86) entrano perché in questo keys.json sono liberi
    giro = {k: v for k, v in leggi(vc / ("keys.json" if sys.platform == "darwin" else "keys-ctrl.json")).get("global", {}).items()
            if v.startswith("arturo.volta-giro-") or v == "arturo.volta-chiudi"}
    attesi2.update(giro)
    # i tasti di serie di Herdr che questo keys.json non ha entrano, sotto quelli già presenti (#5369)
    serie = leggi(vc / ("keys-herdr-macos.json" if sys.platform == "darwin" else "keys-herdr.json"))
    terminale = {fonte[0][0]: TOLTI[0]}
    nuovi_serie = 0
    for sez, dove in (("global", attesi2), ("terminal", terminale)):
        for k, v in serie.get(sez, {}).items():
            if k not in dove:
                dove[k] = v
                nuovi_serie += 1
    if not nuovi_serie:
        return "i tasti di serie di Herdr non sono nella copia di Volta"
    if d["quanti"] != 3 + len(giro) + nuovi_serie or dopo != {"global": attesi2, "terminal": terminale}:
        return f"tasti() di volta_mod.py: {d['quanti']} riallineati, keys.json {dopo}"
    vm = (vc / "volta_mod.py").read_text(encoding="utf-8")
    if vm.count("    try:\n        tasti(fonte)\n") != 1 or vm.index("    try:\n        tasti(fonte)\n") < vm.index("def contorno("):
        return "volta_mod.py: contorno non riallinea i tasti a ogni installazione"
    return None


PROVA_NOMI = r"""
import * as m from "./sessioni.mjs";
const s = (nome, cartella, piu = {}) => ({ id: "ab12cd34", nome, cartella, risposta: "Prima riga", ...piu });
console.log(JSON.stringify({
  progetti: ["-", " _- ", "", null, "uf", "due-mondi", "Due Mondi"].map(m.nomeProgetto),
  senza: m.SENZA,
  titoli: {
    persona: m.titolo(s("bando-57", "/Users/x/Documents/ClaudeCode/tuttovero")),
    personaBarra: m.titolo(s("bando-57", "/Users/x/Documents/ClaudeCode/tuttovero/")),
    windows: m.titolo(s("claudecode-8e", "C:\\Users\\feder\\Documents\\ClaudeCode")),
    spazi: m.titolo(s("volta-celeste-a1", "/x/Volta Celeste/")),
    mac: m.titolo(s("due-mondi-0f", "/x/due-mondi")),
    pezzo: m.titolo(s("mondi-ab", "/x/due-mondi")),
    nonEsa: m.titolo(s("progetto-zz", "/x/progetto")),
    senzaCartella: m.titolo(s("bando-57", undefined)),
    scritto: m.titolo(s("Il mio nome", "/x/y")),
    id: m.titolo(s("ab12cd34", "/x/y")),
    vuoto: m.titolo(s("", "/x/y")),
    conTitolo: m.titolo(s("claudecode-8e", "/x/ClaudeCode", { titolo: "Rifare il deck" })),
  },
  automatici: [m.nomeAutomatico(s("claudecode-8e", "/x/ClaudeCode")), m.nomeAutomatico(s("bando-57", "/x/tuttovero")), m.nomeAutomatico({})],
}));
"""


def hz83(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(repo / "shared/volta/mods/arturo/sessioni.js", casa / "sessioni.mjs")
    (casa / "prova.mjs").write_text(PROVA_NOMI, encoding="utf-8")
    r = subprocess.run([node, str(casa / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["senza"] != "Senza progetto" or d["progetti"] != ["Senza progetto"] * 4 + ["UF", "Due mondi", "Due Mondi"]:
        return f"nomeProgetto: {d['progetti']}"
    attesi = {"persona": "bando-57", "personaBarra": "bando-57", "windows": "Prima riga", "spazi": "Prima riga", "mac": "Prima riga",
              "pezzo": "mondi-ab", "nonEsa": "progetto-zz", "senzaCartella": "Prima riga", "scritto": "Il mio nome",
              "id": "Prima riga", "vuoto": "Prima riga", "conTitolo": "Rifare il deck"}
    for k, v in attesi.items():
        if d["titoli"].get(k) != v:
            return f"titolo, caso {k}: {d['titoli'].get(k)!r}, atteso {v!r}"
    if d["automatici"] != [True, False, True]:
        return f"nomeAutomatico: {d['automatici']}"
    return None


PROVA_SPAZI = r"""
import { eProgetto, progetti } from "./dati.mjs";
const vista = { oggi: "2026-11-11", gruppi: [], progetti: [] };
console.log(JSON.stringify({
  e: [{ name: "Volta", named: true }, { name: "volta", named: true }, { name: "arturo", named: true }, { name: "arturo", named: false },
      { name: "arturo", named: true, machine: "torre" }, { name: "Volta Celeste", named: true }, null, undefined,
      { name: "Senza progetto", named: true }].map(eProgetto),
  chiavi: progetti(vista, { memoria: [] }).map((p) => p.chiave),
}));
"""


def hz84(repo: Path, casa: Path) -> str | None:
    mod_dir = repo / "shared/volta/mods/arturo"
    testata = (mod_dir / "testata.js").read_text(encoding="utf-8")
    if 'bottone("altra"' in testata:
        return "testata.js ha ancora Altra conversazione: la nuova sessione è Nuova richiesta (⌘T), HZ90"
    if 'run("tab.new", { argv: ["claude"] })' in testata:
        return "testata.js apre ancora una scheda con claude dentro, fuori dalla nascita di Volta"
    if 'else if (c === "volta-nuova") this.lungo(c, cx, () => nuovaScheda());' not in (mod_dir / "barra.js").read_text(encoding="utf-8"):
        return "barra.js: arturo.volta-nuova non arriva a nuovaScheda()"
    if 'if (c === "volta-nuova") return { verbo: "volta-nuova", arg: null, lungo: true };' not in (mod_dir / "comandi.js").read_text(encoding="utf-8"):
        return "comandi.js non legge volta-nuova"
    pannello = (mod_dir / "todo.js").read_text(encoding="utf-8")
    corpo = pannello.split("  attivo() {", 1)[-1].split("\n  }\n", 1)[0]
    if "return eProgetto(s) ? slug(s.name) : null;" not in corpo or "eProgetto," not in pannello.split("\n\n", 2)[1]:
        return "todo.js: il progetto attivo non passa da eProgetto"
    node = shutil.which("node")
    if not node:
        return None
    mod = casa / "mod"
    mod.mkdir()
    mod_dati(repo, mod, (mod_dir / "dati.js").read_text(encoding="utf-8"))
    (mod / "prova.mjs").write_text(PROVA_SPAZI, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python3", str(casa / "bin" / "arturo")], "radice": str(repo), "base": str(casa)}), encoding="utf-8")
    herdr = {"spaces": [{"id": "s1", "name": "Volta", "named": True, "active": True}, {"id": "s2", "name": "due-mondi", "named": True},
                        {"id": "s3", "name": "senza-nome", "named": False}, {"id": "s4", "name": "remoto", "named": True, "machine": "torre"}]}
    r = subprocess.run([node, str(mod / "prova.mjs")], capture_output=True, text=True, timeout=30,
                       env={**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_HERDR": json.dumps(herdr)})
    if r.returncode != 0:
        return f"dati.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["e"] != [False, False, True, False, False, True, False, False, False]:
        return f"eProgetto: {d['e']}"
    if d["chiavi"] != ["due-mondi"]:
        return f"fra i progetti della barra: {d['chiavi']}, atteso il solo due-mondi"
    return None


PROVA_SPUNTE = r"""
import { ancoraFatti } from "./azioni.mjs";
const vista = { gruppi: [{ tipo: "tu", todo: [{ id: 1 }, { id: 4 }] }, { tipo: "io", todo: [{ id: 2 }, { id: 3 }] }, { tipo: "fermo" }] };
const prima = new Set([1, 2, 9]);
const dopo = ancoraFatti(prima, vista);
console.log(JSON.stringify({ dopo: [...dopo].sort(), eSet: dopo instanceof Set, altro: dopo !== prima, prima: [...prima],
  vuota: [...ancoraFatti(new Set([1]), null)], nessuna: [...ancoraFatti(undefined, vista)] }));
"""

PROVA_PORTA = r"""
import { portaNome, PORTA_MS } from "./dati.mjs";
import { eseguiti, inviati } from "./herdr.mjs";
let ora = 1700000000000;
Date.now = () => ora;
const s = { id: "ffff1111", sessionId: "ffff1111-aaaa", host: "Torre", macchina: "Torre", nome: "Progetto x", stato: "ferma", tipo: "background",
            daPortare: "Nome mio", attach: ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"] };
const altra = { ...s, id: "eeee2222", sessionId: "eeee2222-bbbb", attach: ["ssh", "-t", "torre.lan", "claude", "attach", "eeee2222"] };
const passi = [];
const passo = async (nome, sess = s) => {
  const esito = await portaNome(sess);
  passi.push([nome, esito, inviati.filter((x) => x[0] === "send").length, eseguiti.filter((x) => x.includes("--portato")).length]);
};
await passo("prima");
ora += 60000; await passo("un minuto dopo");
ora += PORTA_MS - 60001; await passo("un millisecondo prima dei cinque minuti");
ora += 1; await passo("a cinque minuti");
await passo("altra sessione, stesso nome", altra);
await passo("nome nuovo", { ...s, daPortare: "Altro nome" });
console.log(JSON.stringify({ passi, ms: PORTA_MS, scritti: inviati.filter((x) => x[0] === "send") }));
"""


def hz85(repo: Path, casa: Path) -> str | None:
    mod_dir = repo / "shared/volta/mods/arturo"
    pannello = (mod_dir / "todo.js").read_text(encoding="utf-8")
    carica = pannello.split("  carica(cx) {", 1)[-1].split("\n  }\n", 1)[0]
    if "this.fatti = ancoraFatti(this.fatti, r.json);" not in carica or "fatti.clear()" in pannello:
        return "todo.js: una rilettura toglie le spunte messe dalla persona"
    if "ancoraFatti }" not in pannello.split("\n\n", 2)[1]:
        return "todo.js non importa ancoraFatti"
    fatto = pannello.split("  fatto(t, cx) {", 1)[-1].split("\n  }\n", 1)[0]
    scrive, chiama, avvisa = fatto.find('setShared("arturo.scritto", Date.now());'), fatto.find("await todo(fatto(t).argv);"), fatto.find("if (r.ok) notify(")
    if not 0 <= chiama < scrive < avvisa:
        return "todo.js: dopo un todo segnato fatto la barra non rilegge i conti (arturo.scritto)"
    if '|${shared("arturo.scritto") ?? ""}`' not in (mod_dir / "barra.js").read_text(encoding="utf-8"):
        return "barra.js non guarda più arturo.scritto"
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(mod_dir / "azioni.js", casa / "azioni.mjs")
    (casa / "spunte.mjs").write_text(PROVA_SPUNTE, encoding="utf-8")
    r = subprocess.run([node, str(casa / "spunte.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"azioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d != {"dopo": [1, 2], "eSet": True, "altro": True, "prima": [1, 2, 9], "vuota": [], "nessuna": []}:
        return f"ancoraFatti: {d}"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod_dir / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_PORTA, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base", "volta": "/v/volta_sonda.py"}), encoding="utf-8")
    herdr = {"spaces": [{"id": "s1", "name": "progetto-x", "named": True, "active": True, "tabs": [{"id": "tb1"}, {"id": "tb2"}]}],
             "panes": [{"terminal": "t7", "tab": "tb1"}, {"terminal": "t5", "tab": "tb2"}],
             "terminals": [{"address": "t7", "argv": ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]}, {"address": "t5", "argv": ["ssh", "-t", "torre.lan", "claude", "attach", "eeee2222"]}]}
    bordo = "─" * 30
    vuota = f"ciao\n{bordo}\n❯ \n{bordo}\n  stato"

    def giro(**extra):
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_EXEC": json.dumps({"ok": True}),
             "HZ_HERDR": json.dumps(herdr), "HZ_HC_READ": json.dumps({"t7": vuota, "t5": vuota}), **extra}
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[-200:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    try:
        v = giro()
        attesi = [["prima", True, 1, 1], ["un minuto dopo", True, 1, 2], ["un millisecondo prima dei cinque minuti", True, 1, 3],
                  ["a cinque minuti", True, 2, 4], ["altra sessione, stesso nome", True, 3, 5], ["nome nuovo", True, 4, 6]]
        for avuto, atteso in zip(v["passi"], attesi):
            if avuto != atteso:
                return f"/rename, passo {atteso[0]}: esito, scritture e segni alla sonda {avuto[1:]}, attesi {atteso[1:]}"
        if v["ms"] != 300000:
            return f"lo stesso nome non si riscrive per {v['ms']} ms, attesi 5 minuti"
        if v["scritti"] != [["send", "t7", "/rename Nome mio"]] * 2 + [["send", "t5", "/rename Nome mio"], ["send", "t7", "/rename Altro nome"]]:
            return f"/rename scritto nella scheda sbagliata: {v['scritti']}"
        # la sonda non riesce a segnarlo: /rename non si riscrive a ogni lettura, si riprova solo il segno
        v = giro(HZ_EXEC_CODICE="1")
        if [p[1:] for p in v["passi"][:3]] != [[False, 1, 1], [False, 1, 2], [False, 1, 3]]:
            return f"con la sonda che non segna il nome, /rename si riscrive a ogni lettura: {v['passi'][:3]}"
        # /rename non scritto: non conta, alla lettura dopo si riprova a scriverlo
        v = giro(HZ_HC_ROTTO="send")
        if [p[1:] for p in v["passi"][:2]] != [[False, 1, 0], [False, 2, 0]]:
            return f"un /rename non riuscito conta come scritto: {v['passi'][:2]}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    return None


PROVA_GIRO = r"""
const n = await import(%s);
const c = await import(%s);
const bg = (id, stato = "lavora", fine = true) => ({ sessionId: id + "-lungo", id, tipo: "background", attach: ["claude", "attach", id], stato, ...(stato === "ferma" ? { chi: "claude", fineFatta: fine } : {}) });
const g = [{ chiave: "a", sessioni: [bg("a1"), bg("a2", "ferma", false), bg("a3", "ferma"), bg("a4", "ferma"),
    { sessionId: "t1", id: "t1", tipo: "interattiva", stato: "aspetta" }, { sessionId: "f1", id: "f1", tipo: "interattiva", stato: "lavora", vecchia: true }] },
  { chiave: "b", sessioni: [bg("b1", "ferma"), { sessionId: "h1", id: "h1", tipo: "interattiva", terminale: "t9", questa: true, stato: "lavora" }] }];
const o = n.ordineGiro(g, {});
console.log(JSON.stringify({ o, aperto: n.ordineGiro(g, { a: true }), vuoto: n.ordineGiro(null),
  scheda: n.ordineGiro(g, {}, new Set(["qui:a3", "qui:b1"])),
  nuovo: n.statoGiro(null, o, 1000),
  raffica: n.statoGiro({ ids: ["x", "qui:h1", "qui:a1"], ultimo: "qui:h1", quando: 1000 }, o, 1000 + n.GIRO_MS),
  scaduto: n.statoGiro({ ids: ["qui:h1"], ultimo: "qui:h1", quando: 1000 }, o, 1001 + n.GIRO_MS),
  sparite: n.statoGiro({ ids: ["x"], ultimo: "x", quando: 1000 }, o, 2000).ids,
  passi: [n.passoGiro(o, "qui:a1", 1), n.passoGiro(o, "qui:h1", 1), n.passoGiro(o, "qui:a1", -1), n.passoGiro(o, null, 1),
    n.passoGiro(o, null, -1), n.passoGiro([], "a", 1), n.passoGiro(o, "boh", 1)],
  di: [n.sessioneDi({ address: "t5", argv: ["sh", "-c", "claude attach a2"], labels: {} }, g[0].sessioni)?.id ?? null,
    n.sessioneDi({ address: "t5", argv: ["zsh"], labels: { "arturo.sessione": "a3" } }, g[0].sessioni)?.id ?? null,
    n.sessioneDi({ address: "t9", argv: ["zsh"] }, g[1].sessioni)?.id ?? null,
    n.sessioneDi({ address: "t7", argv: ["zsh"] }, g[1].sessioni), n.sessioneDi(null, g[1].sessioni)],
  cmd: [c.instrada("volta-giro-avanti"), c.instrada("volta-giro-indietro"), c.instrada("volta-giro").verbo],
}));
"""


def hz86(repo: Path, casa: Path) -> str | None:
    """⌘↓ e ⌘↑ girano fra le sessioni dell'elenco, di ogni macchina, col gesto del clic."""
    vc = repo / "shared/volta"
    mod = vc / "mods/arturo"
    tasti = leggi(vc / "keys.json").get("global", {})
    if tasti.get("cmd-down") != "arturo.volta-giro-avanti" or tasti.get("cmd-up") != "arturo.volta-giro-indietro":
        return "keys.json non lega ⌘↓ e ⌘↑ al giro fra le sessioni"
    if tasti.get("cmd-shift-down") != "agent.next":
        return "keys.json ha perso ⌘⇧↓ (la prossima sessione che ti aspetta)"
    if 'else if (c === "volta-giro") this.volta.giro(arg, cx);' not in (mod / "barra.js").read_text(encoding="utf-8"):
        return "barra.js non porta arturo.volta-giro-* a Volta.giro()"
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ('const conScheda = new Set(sessioni.filter((s) => (s.questa && s.terminale) || schedeDi(s).length).map(chiave));',
                  "const id = passoGiro(st.ids, st.ultimo ?? (qui ? chiave(qui) : null), verso);",
                  "if (s) { this.scopri(s); this.premi(s, cx); }", "const mostra = mostrate(g, this.aperti[g.chiave]);"):
        if pezzo not in volta:
            return f"volta.js non ha più: {pezzo}"
    if '"arturo.volta-giro-avanti", "arturo.volta-giro-indietro"' not in (vc / "volta_mod.py").read_text(encoding="utf-8"):
        return "volta_mod.py non porta i tasti del giro alle installazioni che ci sono già"
    node = shutil.which("node")
    if not node:
        return None
    for nome in ("sessioni", "comandi"):
        shutil.copyfile(mod / f"{nome}.js", casa / f"{nome}.mjs")
    r = subprocess.run([node, "--input-type=module", "-e",
                        PROVA_GIRO % (json.dumps((casa / "sessioni.mjs").as_uri()), json.dumps((casa / "comandi.mjs").as_uri()))],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    # a2 aspetta un comando ed è accesa: entra (Federico, 12/11 sera). a3, a4 e b1 hanno fatto /fine:
    # senza una scheda restano fuori, il tasto riaprirebbe una sessione chiusa.
    if g["o"] != ["qui:a1", "qui:a2", "qui:h1"]:
        return f"ordineGiro() lascia fuori una sessione accesa che aspetta un comando, o prende una chiusa con /fine o una in un Terminale: {g['o']}"
    if g["aperto"] != ["qui:a1", "qui:a2", "qui:h1"] or g["vuoto"] != []:
        return f"ordineGiro() col gruppo aperto prende le ferme chiuse con /fine senza scheda: {g['aperto']}"
    if g["scheda"] != ["qui:a1", "qui:a2", "qui:a3", "qui:h1", "qui:b1"]:
        return f"ordineGiro() lascia fuori una ferma che ha una scheda aperta, anche nascosta: {g['scheda']}"
    if g["nuovo"] != {"ids": g["o"], "ultimo": None, "quando": 1000}:
        return f"statoGiro() senza un giro prima non parte dall'elenco: {g['nuovo']}"
    if g["raffica"]["ids"] != ["qui:h1", "qui:a1"] or g["raffica"]["ultimo"] != "qui:h1":
        return f"dentro una raffica di tasti l'ordine cambia, o resta una sessione sparita: {g['raffica']}"
    if g["scaduto"]["ids"] != g["o"] or g["scaduto"]["ultimo"] is not None:
        return f"dopo la pausa il giro non riparte dall'elenco di adesso: {g['scaduto']}"
    if g["sparite"] != g["o"]:
        return f"con tutte le sessioni del giro sparite non si riparte dall'elenco: {g['sparite']}"
    if g["passi"] != ["qui:a2", "qui:a1", "qui:h1", "qui:a1", "qui:h1", None, "qui:a1"]:
        return f"passoGiro() non gira in tondo: {g['passi']}"
    if g["di"] != ["a2", "a3", "h1", None, None]:
        return f"sessioneDi() non riconosce la scheda in primo piano: {g['di']}"
    if g["cmd"] != [{"verbo": "volta-giro", "arg": 1, "lungo": False}, {"verbo": "volta-giro", "arg": -1, "lungo": False}, "volta"]:
        return f"instrada() non legge i comandi del giro prima di volta-<id>: {g['cmd']}"
    return None


PROVA_MOTIVO = r"""
import * as m from "./sessioni.mjs";
const torre = { macchina: "Torre", host: "torre.lan" }, qui = { questa: true, macchina: "MacBook" };
const aggancio = "federico@mac ~ % ssh -t torre.lan claude attach ffff1111\n";
const vedi = (schermo, s = torre) => m.motivoUscita(schermo, s);
console.log(JSON.stringify({
  rete: vedi(aggancio + "ssh: connect to host torre.lan port 22: Operation timed out\nfederico@mac ~ % "),
  cartella: vedi(aggancio + "Error: EINTR: interrupted system call, uv_cwd\n"),
  sparita: vedi(aggancio + "No job matching ffff1111\n"),
  colori: vedi(aggancio + "\u001b[31mNot\u001b[1m logged\u001b[0m in · Please run /login\n"),
  init: vedi(aggancio + "Session ffff1111 has exited (exit 1 before init: at Object.<anonymous> (/x/cli.js:12))\n"),
  altro: vedi(aggancio + "Session ffff1111 can't start — out of memory.\n"),
  ultimo: vedi("federico@mac ~ % ssh -t torre.lan claude attach ffff1111\nfederico@torre.lan: Permission denied (publickey).\n" +
               "federico@mac ~ % claude attach ffff1111\nSession ffff1111 has exited (boom)\n"),
  qui: vedi("federico@mac ~ % claude attach ffff1111\nzsh: command not found: claude\n", qui),
  niente: vedi("federico@mac ~ % ls\nDocumenti\n"),
  vuoto: [m.motivoUscita("", torre), m.motivoUscita(null, null)],
}));
"""


def hz87(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    mod = repo / "shared/volta/mods/arturo"
    puro = casa / "puro"
    puro.mkdir()
    shutil.copyfile(mod / "sessioni.js", puro / "sessioni.mjs")
    (puro / "prova.mjs").write_text(PROVA_MOTIVO, encoding="utf-8")
    r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    attesi = (("rete", True, "Torre non si raggiunge via ssh"), ("cartella", True, "Su Torre Claude non riesce a leggere la cartella"),
              ("sparita", True, "Su Torre questa sessione non c'è più"), ("colori", True, "Su Torre Claude non è collegato all'account"),
              ("init", False, "Claude esce prima di iniziare (exit 1 before init)"), ("altro", False, "Su Torre Claude esce appena parte (out of memory)."),
              ("ultimo", False, "Su Torre Claude esce appena parte (boom)."), ("qui", True, "Su questa macchina non trovo il programma claude"))
    for k, fermo, pezzo in attesi:
        v = d.get(k)
        if not v or v.get("fermo") is not fermo or pezzo not in v.get("testo", ""):
            return f"motivoUscita, caso {k}: {v}, atteso fermo {fermo} e la frase {pezzo!r}"
    if "cli.js" in d["init"]["testo"] or "Permission denied" in d["ultimo"]["testo"]:
        return f"motivoUscita porta sulla riga la traccia interna o un tentativo vecchio: {d['init']}, {d['ultimo']}"
    if d["niente"] is not None or d["vuoto"] != [None, None]:
        return f"motivoUscita inventa un motivo: {d['niente']}, {d['vuoto']}"
    # la veglia e le schede remote, su dati.js
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_APRI, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    attach = ["ssh", "-t", "torre.lan", "claude", "attach", "ffff1111"]
    nascita = ["/bin/zsh", "-lic", '"$@"; exec "$0" -li', "/bin/zsh", *attach]
    viva = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 77, "argv": attach}}
    nuda = {"state": "live", "pid": 10, "argv": nascita, "foreground": {"pid": 10, "argv": ["/bin/zsh", "-li"]}}
    spazio = {"id": "s1", "name": "progetto-x", "named": True, "active": True, "tabs": [{"id": "tb0", "name": "Shell"}]}
    herdr = {"spaces": [spazio], "panes": [{"terminal": "t3", "tab": "tb0"}], "terminals": [{"address": "t3", "argv": ["zsh"]}]}
    remota = {"spaces": [spazio], "panes": [{"terminal": "t3", "tab": "tb0"}, {"terminal": "torre/t7", "tab": "tbR"}],
              "terminals": [{"address": "t3", "argv": ["zsh"]},
                            {"address": "torre/t7", "argv": ["claude", "attach", "ffff1111"], "labels": {"arturo.sessione": "ffff1111"}}]}
    aggancio = "federico@mac ~ % ssh -t torre.lan claude attach ffff1111\n"

    def volta(herdr=herdr, letture=None, schermo=None, **extra):
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": "apri", "HZ_EXEC": '{"ok": true}',
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": [], "arturo.dove": "qui"}), "HZ_NASCE": "t9",
             "HZ_HERDR": json.dumps(herdr), "HZ_HC_GET": json.dumps(letture or {}),
             "HZ_HC_READ": json.dumps({} if schermo is None else {"t9": schermo}), **extra}
        for k in ("HZ_STATO", "HZ_PRONTA", "HZ_HC_ROTTO"):
            e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, timeout=30, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:200])
        return json.loads(r.stdout.strip().splitlines()[-1])

    sonda = lambda v: [x[3:] for x in v["eseguiti"] if len(x) > 2 and x[2] == "apri"]  # noqa: E731
    nuove = lambda v: [x for x in v["lanciati"] if x["cmd"] in ("tab.new", "space.new")]  # noqa: E731
    invii = lambda v: [x for x in v["inviati"] if x[0] == "send"]  # noqa: E731
    try:
        # una causa ferma: la riga dice il motivo, niente riavvio e niente rilancio
        v = volta(letture={"t9": [nuda]}, schermo=aggancio + "ssh: connect to host torre.lan port 22: Operation timed out\n")
        errore = (v["veglia"] or {}).get("errore", "")
        if "Torre non si raggiunge via ssh" not in errore:
            return f"la riga non dice perché la sessione non si apre: {v['veglia']}"
        if any("--riavvia" in x for x in sonda(v)) or invii(v):
            return f"una macchina che non si raggiunge viene riavviata e riprovata: {sonda(v)}, {invii(v)}"
        # una causa che può passare: un riavvio solo, e se non basta la riga dice il motivo letto
        v = volta(letture={"t9": [nuda]}, schermo=aggancio + "Session ffff1111 has exited (boom)\n")
        errore = (v["veglia"] or {}).get("errore", "")
        if [x for x in sonda(v) if "--riavvia" in x] != [["Torre", "ffff1111", "--riavvia"]] or len(invii(v)) != 1:
            return f"una sessione uscita per un motivo che può passare non si riavvia una volta sola: {sonda(v)}, {invii(v)}"
        if "Su Torre Claude esce appena parte (boom)." not in errore:
            return f"dopo il riavvio fallito la riga non dice il motivo: {v['veglia']}"
        # uno schermo che non dice niente: la frase generica di prima
        v = volta(letture={"t9": [nuda]}, schermo="federico@mac ~ % ")
        if "non resta aperto" not in (v["veglia"] or {}).get("errore", ""):
            return f"senza un motivo riconoscibile manca la frase generica: {v['veglia']}"
        # la scheda della stessa sessione su un'altra macchina non è una scheda di questa finestra
        v = volta(herdr=remota, letture={"t9": [viva]})
        if v["esito"].get("come") != "nuova" or len(nuove(v)) != 1 or any(x.get("cmd") == "tab.select" and x.get("id") == "tbR" for x in v["lanciati"]):
            return f"una scheda di un'altra macchina passa per scheda di questa finestra: {v['esito']}, {v['lanciati']}"
    except RuntimeError as e:
        return f"dati.js non gira: {e}"
    return None


def _luce(h: str) -> float:
    c = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrasto(a: str, b: str) -> float:
    alto, basso = sorted((_luce(a), _luce(b)), reverse=True)
    return (alto + 0.05) / (basso + 0.05)


def hz88(repo: Path, casa: Path) -> str | None:
    base = repo / "shared/volta"
    for nome in ("arturo", "arturo-carta"):
        t = json.loads((base / f"themes/{nome}.json").read_text(encoding="utf-8"))
        fondo = t["background"]
        for chi, colore, sotto in [("testo", t["foreground"], fondo), ("testo sulla selezione", t["foreground"], t["selection"])] + \
                [(f"ansi {i}", c, fondo) for i, c in enumerate(t["ansi"]) if i]:
            r = contrasto(colore, sotto)
            if r < 4.5:
                return f"tema {nome}: {chi} {colore} su {sotto} è {r:.2f}:1, sotto 4,5:1"
    lay = json.loads((base / "layouts/arturo.json").read_text(encoding="utf-8"))
    cornici = []

    def cerca(n):
        pane = (n.get("content") or {}).get("pane") if isinstance(n.get("content"), dict) else None
        if pane:
            cornici.append(pane)
        for f in n.get("children", []):
            cerca(f)
    cerca(lay)
    if not cornici:
        return "il layout non ha la cornice del terminale (content.pane)"
    for pane in cornici:
        for k in ("border", "focus"):
            c = (pane.get(k) or {}).get("color", "")
            if c.startswith("#"):
                return f"la cornice del terminale ha {k} fisso {c}: col tema chiaro resta uguale, usa un nome del tema"
    return None


PROVA_CONGEDO = r"""
import { visibili, sparite, passoCongedo } from "./sessioni.mjs";
const T = Date.parse("2026-11-12T10:00:00Z");
const s = (x) => ({ tipo: "background", id: "aaaa1111", sessionId: "S1", host: "qui", macchina: "M", stato: "ferma", ultimo: "2026-11-12T09:00:00Z", ...x });
const c = (x) => ({ sessionId: "S1", fase: "attende", da: T, dal: T, ...x });
const out = {};
// il congedo di S3 sta sotto il sessionId, come le voci scritte prima del 14/11 (#5634): vale per la sua chiave
out.vis = visibili({ sessioni: [s({}), s({ sessionId: "S2", id: "b", chiusa: true }), s({ sessionId: "S3", id: "c" }), s({ sessionId: "S4", id: "d", stato: "errore" })] }, { S3: { sessionId: "S3", id: "c", host: "qui" } }).sessioni.map((x) => x.sessionId);
const sc = (n) => ({ sessionId: `S${n}`, id: `i${n}`, host: "qui" });
out.sparite = sparite({ t1: sc(1), t2: sc(2), t3: sc(3), t4: sc(4) }, { t3: sc(3), t9: sc(4) }, { t2: T - 1000 }, T).map((x) => x.sessionId);
out.vecchioTolto = sparite({ t2: sc(2) }, {}, { t2: T - 120000 }, T).map((x) => x.sessionId);
out.primo = sparite(null, { t1: sc(1) }).length;
out.lavora = passoCongedo(c({}), s({ stato: "lavora" }), T + 1000).fai;
out.lavoraTroppo = passoCongedo(c({}), s({ stato: "lavora" }), T + 21 * 60000).fai;
out.ferma = passoCongedo(c({}), s({}), T + 1000);
out.avvio = passoCongedo(c({ fase: "fine" }), s({}), T + 5000).fai;
out.finita = passoCongedo(c({ fase: "fine" }), s({ ultimo: "2026-11-12T10:01:00Z" }), T + 90000);
out.nonFatta = passoCongedo(c({ fase: "fine" }), s({}), T + 4 * 60000);
out.domanda = passoCongedo(c({ fase: "fine" }), s({ stato: "aspetta" }), T + 60000);
out.lunga = passoCongedo(c({ fase: "fine" }), s({ stato: "lavora" }), T + 21 * 60000);
out.chiusaOk = passoCongedo(c({ fase: "ferma" }), s({ chiusa: true }), T + 5000).fai;
out.chiusaSalvata = passoCongedo(c({ fase: "ferma", salvata: true }), s({ chiusa: true }), T + 5000).fai;
out.salvataViva = passoCongedo(c({ fase: "ferma", salvata: true }), s({}), T + 5000).fai;
out.riprova = passoCongedo(c({ fase: "ferma" }), s({}), T + 130000).fai;
out.giaChiusa = passoCongedo(c({}), s({ chiusa: true }), T + 1000).fai;
out.giu = passoCongedo(c({ fase: "fine" }), s({ vecchia: true }), T + 3600000).fai;
console.log(JSON.stringify(out));
"""


def hz89(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    node = shutil.which("node")
    if node:
        puro = casa / "puro"
        puro.mkdir()
        shutil.copyfile(mod / "sessioni.js", puro / "sessioni.mjs")
        (puro / "prova.mjs").write_text(PROVA_CONGEDO, encoding="utf-8")
        r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
        d = json.loads(r.stdout.strip().splitlines()[-1])
        if d["vis"] != ["S1", "S4"]:
            return f"visibili() non toglie le chiuse e quelle in congedo, o toglie quella in errore: {d['vis']}"
        if d["sparite"] != ["S1"] or d["vecchioTolto"] != ["S2"] or d["primo"] != 0:
            return f"sparite() sbaglia le schede chiuse dalla persona: {d['sparite']}, {d['vecchioTolto']}, {d['primo']}"
        attesi = {"lavora": "attendi", "lavoraTroppo": "fine", "avvio": "attendi", "chiusaOk": "togli", "chiusaSalvata": "rm",
                  "salvataViva": "attendi", "riprova": "stop", "giaChiusa": "togli", "giu": "attendi"}
        for k, v in attesi.items():
            if d[k] != v:
                return f"passoCongedo, caso {k}: {d[k]}, atteso {v}"
        if d["ferma"] != {"fai": "fine", "fase": "fine"} or d["finita"] != {"fai": "stop", "fase": "ferma", "salvata": True}:
            return f"passoCongedo non riprende con /fine o non ferma a /fine finito: {d['ferma']}, {d['finita']}"
        for k in ("nonFatta", "domanda", "lunga"):
            if d[k].get("fai") != "stop" or not d[k].get("avviso"):
                return f"passoCongedo, caso {k}: non ferma o non lo dice: {d[k]}"
            if d[k].get("salvata"):
                return f"passoCongedo, caso {k}: segna salvata una sessione senza /fine, e claude rm la perderebbe: {d[k]}"
    # la sonda: congeda con un claude finto, e il campo chiusa
    if os.name != "nt":
        sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
        fbin, fapp, fcasa, lavoro = (casa / n for n in ("fbin", "fapp", "fcasa", "lavoro c"))
        for d_ in (fbin, fapp, fcasa, lavoro):
            d_.mkdir()
        (fapp / "arturo.json").write_text(json.dumps({"base": str(casa)}), encoding="utf-8")
        visto = casa / "claude.log"
        fc = fbin / "claude"
        viva = casa / "viva"
        # agents: la sessione ha un processo solo dopo la ripresa (--bg), come claude vero dopo stop
        fc.write_text("#!/bin/sh\nif [ \"$1\" = agents ]; then if [ -e %s ]; then echo '[{\"id\": \"aaaa1111\", \"sessionId\": \"aaaa1111-bbbb-cccc\", \"pid\": 7}]'; else echo '[]'; fi; exit 0; fi\n"
                      "[ \"$1\" = daemon ] && { echo 'control.sock: reachable'; exit 0; }\n"
                      "[ \"$1\" = --bg ] && touch %s\n"
                      "{ echo \"== $(pwd)\"; printf '%%s\\n' \"$@\"; } >> %s\necho 'Woke session'\n" % (shlex.quote(str(viva)), shlex.quote(str(viva)), shlex.quote(str(visto))), encoding="utf-8")
        fc.chmod(0o755)
        env = {**os.environ, "PATH": f"{fbin}{os.pathsep}{os.environ.get('PATH', '')}", "HOME": str(fcasa), "USERPROFILE": str(fcasa), "HERDR_APP_HOME": str(fapp)}
        r = subprocess.run([sys.executable, str(sonda), "congeda", "qui", "aaaa1111", "aaaa1111-bbbb-cccc", "--cartella", str(lavoro)],
                           capture_output=True, text=True, timeout=90, env=env)
        try:
            esito_ = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return f"congeda non risponde in JSON: {(r.stderr or r.stdout).strip()[-200:]}"
        righe = visto.read_text(encoding="utf-8").split("== ") if visto.exists() else []
        chiamate = [x.strip().splitlines() for x in righe if x.strip()]
        if r.returncode != 0 or not esito_.get("ok"):
            return f"congeda con un claude finto: rc {r.returncode}, {esito_}"
        argv = [c[1:] for c in chiamate]
        if not argv or argv[0] != ["stop", "aaaa1111"]:
            return f"congeda non ferma prima la sessione: {argv}"
        ripresa = [c for c in chiamate if c[1:2] == ["--bg"]]
        if len(ripresa) != 1 or os.path.realpath(ripresa[0][0]) != os.path.realpath(lavoro) or ripresa[0][2:4] != ["--resume", "aaaa1111-bbbb-cccc"] \
                or "--fork-session" in ripresa[0] or not ripresa[0][-1].startswith("/fine"):
            return f"congeda non riprende la stessa conversazione col solo /fine nella sua cartella: {ripresa}"
        if any("rm" in c[1:2] for c in chiamate):
            return f"congeda elimina la sessione: {argv}"
        # una ripresa che non fa ripartire la sessione si riprova una volta, poi è un errore
        viva.unlink()
        fc.write_text(fc.read_text(encoding="utf-8").replace("[ \"$1\" = --bg ] && touch", "[ \"$1\" = --nessuno ] && touch"), encoding="utf-8")
        visto.unlink()
        r = subprocess.run([sys.executable, str(sonda), "congeda", "qui", "aaaa1111", "aaaa1111-bbbb-cccc", "--cartella", str(lavoro)],
                           capture_output=True, text=True, timeout=120, env=env)
        riprese = visto.read_text(encoding="utf-8").count("--resume") if visto.exists() else 0
        if r.returncode == 0 or riprese != 2 or "non riparte" not in r.stdout:
            return f"una ripresa che non fa ripartire la sessione: rc {r.returncode}, riprese {riprese}, {r.stdout.strip()[-160:]}"
        r = subprocess.run([sys.executable, str(sonda), "congeda", "qui", "--all", "x"], capture_output=True, text=True, timeout=30, env=env)
        if r.returncode == 0:
            return "congeda accetta argomenti sbagliati"
        # inizia (#5465): la sessione spostata riparte col solo /inizio del progetto, come il congedo
        fc.write_text(fc.read_text(encoding="utf-8").replace("[ \"$1\" = --nessuno ] && touch", "[ \"$1\" = --bg ] && touch"), encoding="utf-8")
        visto.unlink(missing_ok=True)
        viva.unlink(missing_ok=True)
        r = subprocess.run([sys.executable, str(sonda), "inizia", "qui", "aaaa1111", "aaaa1111-bbbb-cccc", "due-mondi", "--cartella", str(lavoro)],
                           capture_output=True, text=True, timeout=90, env=env)
        chiamate = [x.strip().splitlines() for x in (visto.read_text(encoding="utf-8").split("== ") if visto.exists() else []) if x.strip()]
        ripresa = [c for c in chiamate if c[1:2] == ["--bg"]]
        if r.returncode != 0 or not chiamate or chiamate[0][1:] != ["stop", "aaaa1111"]:
            return f"inizia non ferma prima la sessione: rc {r.returncode}, {r.stdout.strip()[-160:]}, {[c[1:] for c in chiamate]}"
        if len(ripresa) != 1 or ripresa[0][2:4] != ["--resume", "aaaa1111-bbbb-cccc"] or "--fork-session" in ripresa[0] or ripresa[0][-1] != "/inizio due-mondi":
            return f"inizia non riprende la stessa conversazione col solo /inizio del progetto: {ripresa}"
    # righe() è Python puro: gira anche su Windows, fuori dal blocco del claude finto
    sonda = repo / "shared/volta/mods/arturo/volta_sonda.py"
    prova = ("import importlib.util,json,sys\nsp=importlib.util.spec_from_file_location('s',sys.argv[1]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)\n"
             "v={'macchina':'M','host':'qui','questa':True,'target':None,'claude':'claude','sessioni':["
             "{'sessionId':'a1','id':'a1aa','kind':'background','state':'stopped'},"
             "{'sessionId':'b2','id':'b2bb','kind':'background','state':'done','status':'idle','pid':4},"
             "{'sessionId':'c3','id':'c3cc','kind':'background','state':'failed'},"
             "{'sessionId':'d4','id':'d4dd','kind':'background','state':'done'},"
             "{'sessionId':'e5','id':'e5ee','kind':'background','state':'done','fineFatta':True},"
             "{'sessionId':'f6','id':'f6ff','kind':'background','state':'done','spostata':True}]}\n"
             "print(json.dumps([[x['chiusa'], x['dorme']] for x in m.righe([v])]))")
    r = subprocess.run([sys.executable, "-c", prova, str(sonda)], capture_output=True, text=True, timeout=30)
    # chiusa: senza processo e fermata con claude stop, dopo /fine o spostata su un'altra macchina (#5537:
    # claude stop lascia "done" chi aveva finito il turno); dorme: senza processo, ritirata dal servizio
    # di Claude (#5495). Una in errore non è né l'una né l'altra: resta, per Riavvia.
    if r.returncode != 0 or json.loads(r.stdout.strip().splitlines()[-1]) != [[True, False], [False, False], [False, False],
                                                                               [False, True], [True, False], [True, False]]:
        return f"righe() non distingue la sessione chiusa da quella che dorme: {(r.stdout or r.stderr).strip()[-200:]}"
    # Sposta segna la partenza (spostata) e la toglie all'arrivo: lo script SEGNA vero, in una casa finta
    if 'esegui(da, SEGNA, {"sid": sid, "spostata": a or "qui"})' not in (mod / "volta_sposta.py").read_text(encoding="utf-8"):
        return "Sposta non segna spostata la conversazione sulla macchina di partenza (#5537)"
    with tempfile.TemporaryDirectory() as t:
        prova = ("import base64,json,os,subprocess,sys\nsys.path.insert(0,sys.argv[1])\nimport volta_sposta as v\n"
                 "def segna(d):\n"
                 "    subprocess.run([sys.executable,'-c',v.SEGNA,base64.b64encode(json.dumps(d).encode()).decode()],check=True,capture_output=True)\n"
                 "    return json.load(open(os.path.join(sys.argv[2],'cache','scheda','s1.json'),encoding='utf-8'))\n"
                 "a=segna({'sid':'s1','spostata':'torre'}); b=segna({'sid':'s1','progetto':'x'}); c=segna({'sid':'s1','progetto':None})\n"
                 "print(json.dumps([a.get('spostata',{}).get('su'), 'spostata' in b, b.get('progetto'), 'spostata' in c, c.get('progetto')]))")
        env = dict(os.environ, CLAUDE_CONFIG_DIR=t, HERDR_APP_HOME=t)
        r = subprocess.run([sys.executable, "-c", prova, str(mod), t], capture_output=True, text=True, timeout=60, env=env)
        if r.returncode != 0 or json.loads(r.stdout.strip().splitlines()[-1]) != ["torre", False, "x", False, "x"]:
            return f"SEGNA non segna e non toglie spostata come deve: {(r.stdout or r.stderr).strip()[-200:]}"
    # la scheda appena chiusa da Volta non passa per quella della sessione arrivata con lo stesso id
    if "!(tolti[x.address] && Date.now() - tolti[x.address] < TOLTI_MS)" not in (mod / "dati.js").read_text(encoding="utf-8"):
        return "schedeDi conta anche le schede che Volta ha appena chiuso (#5537)"
    # il clic per id (herdr-app do, ⌘K) prende prima la riga visibile: la copia chiusa di partenza ha lo stesso id
    if "const l = [this.vis()?.sessioni, this.dati?.sessioni].map(tra).find((x) => x.length) ?? [];" not in (mod / "volta.js").read_text(encoding="utf-8"):
        return "trovaId prende la copia chiusa di partenza prima della sessione visibile (#5537)"
    # le schede che agganciano la sessione si chiudono prima dello spostamento: un attach aperto la riaccende dopo stop
    dj = (mod / "dati.js").read_text(encoding="utf-8")
    i, j = dj.find("  const chiuse = chiudiSchede(s);"), dj.find("r = esito(await exec(c.arturo[0], [c.volta, \"sposta\"")
    if i < 0 or j < 0 or i > j or "const x = await fineSposta(s, macchina, p.errore ? { errore: p.errore } : p.fatto, v.chiuse);" not in dj:
        return "Sposta non chiude le schede della sessione prima di fermarla, o non le riapre se non va (#5537)"
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    dati = (mod / "dati.js").read_text(encoding="utf-8")
    if "cx.timer.every(OGNI_SCHEDE, (cx) => this.guardaSchede(cx));" not in volta or "sparite(this.schede, adesso" not in volta:
        return "volta.js non guarda le schede chiuse"
    if "    chiudiSchede(s);\n    this.congeda(s, cx);" not in volta:
        return "Chiudi del menu non passa dal congedo"
    if 'p.fai === "rm" ? "rm" : "stop"' not in volta or "...(p.salvata ? { salvata: true } : {})" not in volta:
        return "volta.js non elimina con claude rm la sessione salvata, o non tiene salvata nel registro dei congedi"
    if "gruppi(this.vis(), modo)" not in volta or "gruppi(this.dati," in volta:
        return "l'elenco mostra ancora le sessioni chiuse e quelle in congedo"
    if dati.count("segnaTolto(t.address)") != 2:
        return "dati.js non segna le schede che chiude Volta stessa (Chiudi, Sposta, Stacca)"
    return None


PROVA_COLONNA = r'''
import { macchinaBreve, dettaglio, impostaProgetti, nomeProgetto, gruppi, filtraProgetti } from "./sessioni.mjs";
const out = {};
out.brevi = ["MacBook Air di Federico (156)", "Mac Studio di Ufficio", "amaltea", "Federico's MacBook Pro"].map(macchinaBreve);
out.dettaglio = dettaglio({ macchina: "MacBook Air di Federico (156)", stato: "lavora" }, "progetto").testo;
out.prima = nomeProgetto("herdr-arturo");
const v = { chiave: "herdr-arturo", titolo: "Volta" };
impostaProgetti({ "herdr-arturo": v, "volta-celeste": v, "post-studio": { chiave: "post-studio", titolo: "Post Office" } });
out.dopo = [nomeProgetto("herdr-arturo"), nomeProgetto("volta-celeste"), nomeProgetto("post-studio"), nomeProgetto("due-mondi")];
const d = { sessioni: [{ sessionId: "a", id: "a1", progetto: "volta-celeste", ultimo: "2026-11-12T09:00:00Z" },
  { sessionId: "b", id: "b1", progetto: "herdr-arturo", ultimo: "2026-11-12T08:00:00Z" }, { sessionId: "c", id: "c1", progetto: "post-studio" }] };
out.gruppi = gruppi(d, "progetto").map((g) => [g.chiave, g.titolo, g.sessioni.length]);
out.filtro = filtraProgetti(["post-studio", "herdr-arturo", "uf"], "volta");
console.log(JSON.stringify(out));
'''


def hz90(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    testata = (mod / "testata.js").read_text(encoding="utf-8")
    dati = (mod / "dati.js").read_text(encoding="utf-8")
    if "progetti-elenco" in barra or "sezioni(" in barra or ".child(corpo.child(contenuto))" in barra:
        return "la barra ha ancora la sezione dei progetti aperti"
    if 'v_flex().id("volta").flex_1().min_h(0)' not in volta or "tetti(" in volta or 'child("Tutte le sessioni")' in volta:
        return "l'elenco di Volta non prende tutta l'altezza della colonna"
    if ".when(progetto, (el) => el.on_click(() => apriProgetto(g.chiave))\n" not in volta:
        return "l'intestazione di un gruppo per progetto non apre il progetto"
    if 'bottone("chiedi"' in testata or 'bottone("altra"' in testata:
        return "la testata ha ancora Cosa posso chiedere o Altra conversazione"
    if 'shared("arturo.volta.dove")' not in testata or "testata-dove" not in testata or "const macchina = tab ? (dv?.schede?.[term] ?? dv?.qui ?? null) : null;" not in testata:
        return "la testata non dice la macchina della sessione"
    if 'setShared("arturo.volta.dove", m)' not in volta:
        return "volta.js non pubblica la macchina delle schede"
    if "Conversazione aperta" in dati:
        return "lo stato idle si legge ancora Conversazione aperta"
    return hz_colonna_node(repo, casa, "HZ90")


def hz_colonna_node(repo: Path, casa: Path, caso: str) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    puro = casa / f"puro-{caso}"
    puro.mkdir()
    shutil.copyfile(repo / "shared/volta/mods/arturo/sessioni.js", puro / "sessioni.mjs")
    (puro / "prova.mjs").write_text(PROVA_COLONNA, encoding="utf-8")
    r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if caso == "HZ90":
        if d["brevi"] != ["MacBook Air", "Mac Studio", "amaltea", "MacBook Pro"] or d["dettaglio"] != "MacBook Air · Sta lavorando":
            return f"macchinaBreve o dettaglio: {d['brevi']}, {d['dettaglio']}"
        return None
    if d["prima"] != "Herdr arturo" or d["dopo"] != ["Volta", "Volta", "Post Office", "Due mondi"]:
        return f"nomeProgetto senza e con la mappa: {d['prima']}, {d['dopo']}"
    if d["gruppi"] != [["herdr-arturo", "Volta", 2], ["post-studio", "Post Office", 1]]:
        return f"gruppi() non mette il nome alternativo nel gruppo del progetto: {d['gruppi']}"
    if d["filtro"] != ["herdr-arturo"]:
        return f"filtraProgetti non trova il progetto dal titolo: {d['filtro']}"
    return None


def hz91(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    cambio = (mod / "cambio.js").read_text(encoding="utf-8")
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    if volta.count('impostaProgetti(shared("arturo.progetti"));') != 2 or 'impostaProgetti(shared("arturo.progetti"));' not in cambio:
        return "volta.js o cambio.js non impostano i titoli prima del disegno"
    if "mappa[p.chiave] = { chiave: p.chiave," not in barra:
        return "la barra non porta la chiave del progetto nella mappa"
    if "if (m.titolo) v.titolo = m.titolo;" not in (mod / "dati.js").read_text(encoding="utf-8"):
        return "progetti() di dati.js perde il titolo della memoria per un progetto coi todo"
    return hz_colonna_node(repo, casa, "HZ91")



PROVA_FASI = r"""
import * as n from "./sessioni.mjs";
const T = Date.parse("2026-11-12T12:00:00Z");
const s = (x) => ({ tipo: "background", id: "aaaa1111", sessionId: "S1", host: "qui", macchina: "M", questa: true, stato: "ferma",
  chi: "claude", interazione: "2026-11-12T10:00:00Z", ultimo: "2026-11-12T10:00:00Z", coda: "Fatto.", ...x });
const code = {
  scrivimi: "Prova ⌘W su una scheda di sessione e scrivimi **chiude** oppure **niente**.",
  numeri: "I caroselli restano a una pagina.\n\nScrivimi **1**, **2** con il link della cartella, oppure **3**.",
  domanda: "Ho due strade per il deck. Preferisci la prima?",
  domandaPrima: "Va bene così?\n\nDettagli su richiesta.",
  tuo: "Prossimo passo: rileggi e invia le tre bozze (tu), poi confronto.",
  bang: "Lancia questo:\n\n! gh auth login\n",
  niente: "Fatto: il terminale è a posto.\n\nNiente da fare per te.",
  altri: "Prossimo passo: domani mattina Tommaso fa le due registrazioni; appena arrivano i documenti li leggo io.",
  claude: "Prossimo passo: Claude fa il passo 5 del piano.",
};
const out = { fasi: {} };
for (const [k, coda] of Object.entries(code)) out.fasi[k] = n.fase(s({ coda }));
out.persona = n.fase(s({ chi: "persona", coda: "" }));
out.azione = n.fase(s({ chi: "azione" }));
out.senza = n.fase(s({ chi: undefined }));
out.aspetta = n.fase(s({ stato: "aspetta", coda: code.niente }));
out.permesso = n.fase(s({ aspetta: "permission prompt", coda: code.niente }));
out.lavora = n.fase(s({ stato: "lavora" }));
out.errore = n.fase(s({ stato: "errore" }));
out.chiusa = n.fase(s({ chiusa: true }));
out.frasi = [n.fraseStato(s({ coda: code.niente }), T), n.fraseStato(s({ coda: code.scrivimi }), T), n.fraseStato(s({ coda: code.niente, interazione: "" }), T)];
const g = { chiave: "p", sessioni: [s({ sessionId: "A", coda: code.niente }), s({ sessionId: "B", coda: code.scrivimi }), s({ sessionId: "C", coda: code.niente }), s({ sessionId: "D", coda: code.niente })] };
out.chiuso = n.mostrate(g, false).map((x) => x.sessionId);
out.aperto = n.mostrate(g, true).map((x) => x.sessionId);
out.poche = n.mostrate({ chiave: "q", sessioni: [s({ sessionId: "E", coda: code.niente })] }, false).map((x) => x.sessionId);
console.log(JSON.stringify(out));
"""


def hz92(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ("const vive = g.sessioni.filter((s) => !inAttesa(s));", "`${ferme.length} in attesa di comando`",
                  "const vivo = !s.vecchia && !inAttesa(s);"):
        if pezzo not in vj:
            return f"volta.js non ha più: {pezzo}"
    sonda = mod / "volta_sonda.py"
    # La sonda sulla trascrizione: una sessione che ha chiuso il turno con un testo, dopo un /fine.
    radice = casa / ".claude"
    (radice / "projects" / "p").mkdir(parents=True)
    righe = [
        {"type": "summary"},
        {"type": "user", "timestamp": "2026-11-12T09:00:00Z", "message": {"role": "user", "content": "<command-message>fine</command-message>\n<command-name>/fine</command-name>"}},
        {"type": "assistant", "timestamp": "2026-11-12T09:01:00Z", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}},
        {"type": "user", "timestamp": "2026-11-12T09:02:00Z", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
        {"type": "assistant", "timestamp": "2026-11-12T09:03:00Z", "message": {"content": [{"type": "text", "text": "Fatto: handoff scritto.\n\nNiente da fare per te."}]}},
        {"type": "user", "isMeta": True, "timestamp": "2026-11-12T09:30:00Z", "message": {"content": "<system-reminder>x</system-reminder>"}},
        {"type": "system", "timestamp": "2026-11-12T09:40:00Z"},
    ]
    (radice / "projects" / "p" / "sid-uno.jsonl").write_text("\n".join(json.dumps(r) for r in righe) + "\n", encoding="utf-8")
    finto = casa / "claude"
    finto.write_text("#!/bin/sh\necho '[{\"id\":\"lav1\",\"sessionId\":\"sid-uno\",\"kind\":\"background\",\"state\":\"done\",\"status\":\"idle\",\"pid\":5,\"startedAt\":9999999999999,\"cwd\":\"/tmp\"}]'\n", encoding="utf-8")
    finto.chmod(0o755)
    if os.name == "nt":
        return None
    codice = ("import importlib.util, json, sys\n"
              "spec = importlib.util.spec_from_file_location('vs', sys.argv[1]); vs = importlib.util.module_from_spec(spec); spec.loader.exec_module(vs)\n"
              "g = {'T': 20, '__name__': 'sonda'}\n"
              "src = vs.SONDA.replace('cl = trova_claude()', 'cl = sys.argv[1] or trova_claude()')\n"
              "sys.argv = [sys.argv[0], sys.argv[2]]\n"
              "exec(compile(src, 'sonda', 'exec'), g)\n")
    r = subprocess.run([sys.executable, "-c", codice, str(sonda), str(finto)], capture_output=True, text=True, timeout=60,
                       env={**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "CLAUDE_CONFIG_DIR": str(radice), "HERDR_APP_HOME": str(casa / "app")})
    try:
        voce = json.loads(r.stdout.strip().splitlines()[-1])["sessioni"][0]
    except (ValueError, IndexError, KeyError):
        return f"la sonda non dà la sessione: {(r.stderr or r.stdout).strip()[-200:]}"
    attesi = {"interazione": "2026-11-12T09:03:00Z", "chi": "claude", "fineFatta": True, "ultimo": "2026-11-12T09:40:00Z"}
    for k, v in attesi.items():
        if voce.get(k) != v:
            return f"la sonda, campo {k}: {voce.get(k)!r}, atteso {v!r}"
    if not str(voce.get("coda", "")).endswith("Niente da fare per te."):
        return f"la sonda non passa la fine dell'ultimo testo di Claude: {voce.get('coda')!r}"
    vs = sonda.read_text(encoding="utf-8")
    if '"interazione": s.get("interazione") or "", "coda": (s.get("coda") or "")[-300:],' not in vs or '"chi": s.get("chi") or "", "fineFatta": s.get("fineFatta") is True,' not in vs:
        return "righe() non porta nell'elenco interazione, coda, chi e fineFatta"
    node = shutil.which("node")
    if not node:
        return None
    puro = casa / "puro"
    puro.mkdir()
    shutil.copyfile(mod / "sessioni.js", puro / "sessioni.mjs")
    (puro / "prova.mjs").write_text(PROVA_FASI, encoding="utf-8")
    r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    fasi = {"scrivimi": "stasi", "numeri": "stasi", "domanda": "stasi", "domandaPrima": "stasi", "tuo": "stasi", "bang": "stasi",
            "niente": "attesa", "altri": "attesa", "claude": "attesa"}
    for k, v in fasi.items():
        if d["fasi"][k] != v:
            return f"fase(), coda {k}: {d['fasi'][k]}, attesa {v}"
    altri = {"persona": "stasi", "azione": "stasi", "senza": "stasi", "aspetta": "stasi", "permesso": "stasi", "lavora": "attiva",
             "errore": "errore", "chiusa": "chiusa"}
    for k, v in altri.items():
        if d[k] != v:
            return f"fase(), caso {k}: {d[k]}, atteso {v}"
    frasi = [{"testo": "Aspetta un comando da 2 ore", "colore": "muted"}, {"testo": "Ti aspetta da 2 ore", "colore": "blocked"},
             {"testo": "Aspetta un comando da 2 ore", "colore": "muted"}]
    if d["frasi"] != frasi:
        return f"fraseStato() non distingue chi ti aspetta da chi aspetta un comando: {d['frasi']}"
    if d["chiuso"] != ["B"] or d["aperto"] != ["A", "B", "C", "D"] or d["poche"] != ["E"]:
        return f"mostrate() non tiene a vista chi ti aspetta o non nasconde chi aspetta un comando: {d['chiuso']}, {d['aperto']}, {d['poche']}"
    return None


PROVA_AUTO = r"""
import * as n from "./sessioni.mjs";
const T = Date.parse("2026-11-12T12:00:00Z");
const ore = (h) => new Date(T - h * 3600000).toISOString();
const s = (id, x = {}) => ({ tipo: "background", id, sessionId: "S" + id, host: "qui", macchina: "M", questa: true, stato: "ferma",
  chi: "claude", interazione: ore(2), coda: "Niente da fare per te.", ...x });
const dati = { sessioni: [
  s("a"), s("vecchia3", { interazione: ore(3) }), s("fresca", { interazione: ore(0.5) }), s("altrove", { questa: false }),
  s("inter", { tipo: "interattiva" }), s("chiede", { coda: "Scrivimi **sì**." }), s("congedo"), s("scheda"),
  s("incorso", { coda: "Lo lascio in background e ti aggiorno appena finisce." }), s("letta", { vecchia: true }),
  s("lavora", { stato: "lavora" }), s("senzaora", { interazione: "", ultimo: "" }),
] };
// congedi e schede per chiave macchina:id (#5634)
const opz = { dopoMin: 60, congedi: { "qui:congedo": { sessionId: "Scongedo", id: "congedo", host: "qui" } }, conScheda: new Set(["qui:scheda"]) };
const out = {};
out.scelte = n.daCongedare(dati, T, opz).map((x) => x.id);
out.soglia = n.daCongedare(dati, T, { ...opz, dopoMin: 20 }).map((x) => x.id);
out.restanti = [n.restanti([], T), n.restanti([T - 600000, T - 1200000], T), n.restanti([T - 600000, T - 1200000, T - 1800000], T),
  n.restanti(Array.from({ length: 12 }, (_, i) => T - (2 + i) * 3600000), T), n.restanti([T - 600000], T, { ora: 1, giorno: 12 }),
  n.restanti([T + 600000], T)];
const p1 = n.registroProva([], [s("a")], T - 60000);
const p2 = n.registroProva(p1, [s("a"), s("b")], T);
out.prova = p2.map((v) => [v.id, v.vista, v.ultima]);
out.dopoFine = n.passoCongedo({ sessionId: "Sa", fase: "attende", da: T, dal: T, fineFatta: true, auto: true }, s("a"), T + 1000);
out.senzaFine = n.passoCongedo({ sessionId: "Sa", fase: "attende", da: T, dal: T, auto: true }, s("a"), T + 1000);
console.log(JSON.stringify(out));
"""


def hz93(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    inizio = vj.find("  async congedaFerme(cx) {")
    if inizio < 0:
        return "volta.js non ha la chiusura automatica (congedaFerme)"
    corpo = vj[inizio:vj.find("\n  }\n", inizio)]
    for pezzo in ('if (cfg.modo === "spento") return;', "const s = scelte[0];", "if (!scelte.length || restanti(fatti, adesso, cfg) < 1) return;",
                  "this.congeda({ sessionId: s.sessionId, id: s.id, host: s.host ?? \"qui\", auto: true }, cx);", "const conScheda = new Set(Object.values(this.schede ?? {})"):
        if pezzo not in corpo:
            return f"congedaFerme non ha più: {pezzo}"
    a = corpo.find('if (cfg.modo === "prova")')
    prova = corpo[a:corpo.find("const s = scelte[0];")] if a >= 0 else ""
    if not prova or "this.congeda(" in prova or "writeTextFile(file," not in prova or "return;" not in prova:
        return "in modo prova congedaFerme non si limita a scrivere il registro"
    if corpo.count(", testo);") < 2:
        return "congedaFerme non scrive il registro col testo letto prima: due finestre chiuderebbero la stessa sessione"
    if "cx.timer.every(OGNI_AUTO, (cx) => this.congedaFerme(cx));" not in vj:
        return "volta.js non guarda le sessioni da chiudere a intervalli"
    dj = (mod / "dati.js").read_text(encoding="utf-8")
    if 'modo: ["prova", "acceso", "spento"].includes(c.congedo) ? c.congedo : "prova",' not in dj:
        return "dati.js: la chiusura automatica non parte in modo prova"
    if '...(c.auto ? ["--auto"] : [])' not in dj:
        return "dati.js non dice alla sonda che il congedo è automatico"
    vs = (mod / "volta_sonda.py").read_text(encoding="utf-8")
    if "PROMPT_CONGEDO_AUTO if auto else PROMPT_CONGEDO" not in vs or '"rm"' in vs[vs.find("def congeda("):vs.find("CAMBI = ")]:
        return "volta_sonda.py: congeda --auto non usa il suo testo di /fine, o chiama rm"
    node = shutil.which("node")
    if not node:
        return None
    puro = casa / "puro"
    puro.mkdir()
    shutil.copyfile(mod / "sessioni.js", puro / "sessioni.mjs")
    (puro / "prova.mjs").write_text(PROVA_AUTO, encoding="utf-8")
    r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["scelte"] != ["vecchia3", "a"]:
        return f"daCongedare() sbaglia chi chiudere o l'ordine: {d['scelte']}"
    if d["soglia"] != ["vecchia3", "a", "fresca"]:
        return f"daCongedare() non usa la soglia di arturo.json: {d['soglia']}"
    if d["restanti"] != [3, 1, 0, 0, 0, 3]:
        return f"restanti() non tiene i tetti di 3 all'ora e 12 al giorno: {d['restanti']}"
    if sorted(map(tuple, d["prova"])) != [("a", Date_T - 60000, Date_T), ("b", Date_T, Date_T)]:
        return f"registroProva() non tiene la prima volta che ha visto una sessione: {d['prova']}"
    if d["dopoFine"] != {"fai": "stop", "fase": "ferma", "salvata": True}:
        return f"passoCongedo() rifà /fine su una sessione che l'ha già fatto: {d['dopoFine']}"
    if d["senzaFine"] != {"fai": "fine", "fase": "fine"}:
        return f"passoCongedo() non fa /fine nella chiusura automatica: {d['senzaFine']}"
    return None


PROVA_MOTO = r"""
import * as m from "./sessioni.mjs";
import { instrada } from "./comandi.mjs";
const d = (...ids) => ({ sessioni: ids.map((id) => ({ sessionId: `s-${id}`, id, host: "qui" })) });
const out = {
  primaLettura: m.entrate(null, d("a", "b")),
  nuove: m.entrate(d("a", "b"), d("b", "c", "a", "d")),
  senzaId: m.entrate(d("a"), { sessioni: [{ sessionId: "s-x", id: "" }, { sessionId: "s-e", id: "e" }] }),
  prima: m.motoRiga({ fase: "prima", ritardo: 60 }, false),
  via: m.motoRiga({ fase: "via", ritardo: 60 }, false),
  ferma: m.motoRiga(undefined, false),
  esce: m.motoRiga({ fase: "via", ritardo: 0 }, true),
  scala: [0, 1, 2, 3, 4, 9].map(m.ritardo),
  tempi: [m.ENTRA.duration, m.ESCE.duration, m.SCALA_MAX],
  comandi: ["movimento", "movimento-acceso", "movimento-spento", "impostazioni"].map((c) => instrada(c)),
};
console.log(JSON.stringify(out));
"""


def hz94(repo: Path, casa: Path) -> str | None:
    """Le animazioni di Volta (#5410): righe in dissolvenza e interruttore del movimento, che segue "Riduci
    movimento" del Mac. Dal 13/11/2026 (#5488) i segni sono fermi: nessun .spin né .loop nel mod."""
    mod = repo / "shared/volta/mods/arturo"
    if not (mod / "stella-lavora.svg").is_file():
        return "manca stella-lavora.svg, il segno di chi lavora"
    cj = (mod / "comuni.js").read_text(encoding="utf-8")
    for pezzo in ('export const movimento = () => shared("arturo.movimento") !== false && shared("arturo.movimento.ridotto") !== true;',
                  'if (moto !== "gira") return punto(colore, d);', 'svg("mods/arturo/stella-lavora.svg")',
                  'run("app.settings")', 'setShared("arturo.movimento", v);'):
        if pezzo not in cj:
            return f"comuni.js non ha più: {pezzo}"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ("const mr = movimento() ? motoRiga(this.entrano.get(k), this.escono[k]) : null;",
                  "if (!c.uscita && this.esce(s, c, cx)) return;", "this.congeda({ ...c, uscita: true }, cx);",
                  "if (!ids?.length || !cx || !movimento()) return;", "this.entra(entrate(prima, this.dati), cx);",
                  '"com.apple.universalaccess", "reduceMotion"', 'segno(colore(t, d.colore), motoDi(d.colore,', 'fase(s) === "stasi")'):
        if pezzo not in vj:
            return f"volta.js non ha più: {pezzo}"
    esce = vj[vj.find("  esce(s, c, cx) {"):]
    esce = esce[:esce.find("\n  }\n")]
    if "if (!movimento()) return false;" not in esce:
        return "esce() ritarda il congedo anche col movimento spento"
    bj = (mod / "barra.js").read_text(encoding="utf-8")
    if 'else if (c === "impostazioni") apriImpostazioni();' not in bj:
        return "barra.js non apre il menu di Impostazioni col comando arturo.impostazioni"
    # segni fermi (Federico, 13/11/2026, #5488): un'animazione continua ridisegna la finestra 30 volte al secondo
    for f in sorted(mod.glob("*.js")):
        testo = f.read_text(encoding="utf-8")
        if ".spin(" in testo or ".loop(" in testo:
            return f"{f.name} ha ancora un'animazione continua (.spin o .loop): Volta torna al 35% di CPU"
    if '      .child(stella)' not in bj or "apriImpostazioni()" not in bj or 'c === "movimento") giraMovimento(arg)' not in bj:
        return "barra.js: la stella del marchio non è ferma, o Impostazioni non apre l'interruttore"
    mj = (mod / "main.js").read_text(encoding="utf-8")
    if "impostazioni: Impostazioni" not in mj:
        return "main.js non conosce la parte impostazioni"
    node = shutil.which("node")
    if not node:
        return None
    puro = casa / "puro"
    puro.mkdir()
    shutil.copyfile(mod / "sessioni.js", puro / "sessioni.mjs")
    shutil.copyfile(mod / "comandi.js", puro / "comandi.mjs")
    (puro / "prova.mjs").write_text(PROVA_MOTO, encoding="utf-8")
    r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js o comandi.js non girano: {(r.stderr or r.stdout).strip()[-200:]}"
    o = json.loads(r.stdout.strip().splitlines()[-1])
    if o["primaLettura"] != [] or o["nuove"] != ["qui:c", "qui:d"] or o["senzaId"] != ["qui:e"]:
        return f"entrate() sbaglia le righe nuove: {o['primaLettura']} {o['nuove']} {o['senzaId']}"
    if o["prima"] != {"opacita": 0, "politica": None}:
        return f"una riga che entra non parte da 0 senza transizione: {o['prima']}"
    if o["via"] != {"opacita": 1, "politica": {"duration": 180, "easing": "ease-out", "delay": 60}}:
        return f"una riga che entra non va a 1 col suo ritardo: {o['via']}"
    if o["ferma"]["opacita"] != 1 or o["esce"]["opacita"] != 0 or o["esce"]["politica"]["easing"] != "ease-in":
        return f"motoRiga() sbaglia riga ferma o riga che esce: {o['ferma']} {o['esce']}"
    if o["scala"] != [0, 30, 60, 90, 120, 120]:
        return f"la scala dei ritardi non si ferma a 120 ms: {o['scala']}"
    entra, esce_ms, scala = o["tempi"]
    if not (esce_ms < entra <= 300 and entra + scala <= 300):
        return f"tempi fuori dal tetto (uscita più corta dell'entrata, tutto entro 300 ms): {o['tempi']}"
    attesi = [{"verbo": "movimento", "arg": None, "lungo": False}, {"verbo": "movimento", "arg": True, "lungo": False},
              {"verbo": "movimento", "arg": False, "lungo": False}, {"verbo": "impostazioni", "arg": None, "lungo": False}]
    if o["comandi"] != attesi:
        return f"instrada() non conosce i comandi del movimento: {o['comandi']}"
    return None


PROVA_TESSERE = r"""
const m = await import("./tessere.mjs");
const { instrada } = await import("./comandi.mjs");
const l = [{ chiave: "sei-ore", titolo: "Sei ore" }, { chiave: "celestiale", titolo: "Celestiale" },
  { chiave: "arturo", titolo: "Arturo" }, { chiave: "radio-lago", titolo: "Radio Lago" }, null, { titolo: "senza chiave" },
  { chiave: "solaris", titolo: "Solaris" }];
console.log(JSON.stringify({
  vuoto: m.tessere(l, "").map((t) => t.chiave || t.tipo), nessuno: m.tessere(null, "").map((t) => t.tipo),
  ra: m.tessere(l, "ra").map((t) => t.chiave), dentro: m.tessere(l, " IALE ").map((t) => t.chiave),
  s: m.tessere(l, "s").map((t) => t.chiave),
  col: [0, m.MIN_W - 1, m.MIN_W, 2 * m.MIN_W + m.GAP - 1, 2 * m.MIN_W + m.GAP].map(m.colonne),
  passi: [m.passo(0, "right", 10, 4), m.passo(9, "right", 10, 4), m.passo(0, "left", 10, 4), m.passo(1, "down", 10, 4),
    m.passo(8, "down", 10, 4), m.passo(5, "down", 10, 4), m.passo(2, "up", 10, 4), m.passo(6, "up", 10, 4),
    m.passo(3, "x", 10, 4), m.passo(0, "down", 0, 4)],
  iniziali: ["Sei ore", "celestiale", "Due-Mondi", "", "è bello"].map(m.iniziali),
  tinta: [m.tinta("arturo"), m.tinta("arturo"), m.tinta("sei-ore")],
  img: [m.immagine("arturo", new Set(["arturo"])), m.immagine("x", new Set(["arturo"])), m.immagine("arturo", null)],
  nuova: m.NUOVA, stack: [m.STACK, m.TERMINALE, m.CASA],
  comandi: ["casa", "casa-chiudi"].map((c) => instrada(c)),
}));
// #5456: il layout con o senza tessere, le tessere mostrate, e una nota sulle tessere che non va al terminale.
const fs = await import("node:fs");
const n = await import("./nota.mjs");
const lay = JSON.parse(fs.readFileSync(new URL("./arturo.json", import.meta.url), "utf-8"));
const su = structuredClone(lay);
(function f(x) { if (x?.id === "lavoro") x.active = "casa"; for (const c of x?.children ?? []) f(c); })(su);
const senza = { id: "radice", type: "row", children: [{ id: "main", type: "block" }] };
const parti = { marchio: { larghezza: 292, altezza: 54 }, barra: { larghezza: 292, altezza: 690 }, piede: { larghezza: 292, altezza: 156 },
  testata: { larghezza: 1147, altezza: 54 }, stato: { larghezza: 1147, altezza: 40 }, todo: { larghezza: 340, altezza: 700 } };
const fin = { larghezza: 1440, altezza: 900 };
const el = [{ id: "misura-casa", view: 9, x: 305, y: 66, width: 800, height: 780 }, { id: "casa-arturo", view: 9, x: 330, y: 200, width: 200, height: 160 }];
const r = (l) => n.regione({ x: 700, y: 400 }, n.misureDaLayout(l, parti, fin));
console.log(JSON.stringify({
  ha: [m.haTessere(lay), m.haTessere(senza), m.haTessere(null)],
  senza: [m.senzaTessere(lay), m.senzaTessere(senza), m.senzaTessere(null)],
  mostrate: [m.tessereMostrate(lay), m.tessereMostrate(su), m.tessereMostrate(senza)],
  regione: [r(lay)?.blocco, r(su)?.blocco, r(su)?.parte],
  sotto: n.elementoSotto({ x: 400, y: 250 }, el),
  nomi: ["casa-tessere", "casa-nuova", "casa-arturo", "altra"].map(n.nomeElemento),
}));
"""


def hz96(repo: Path, casa: Path) -> str | None:
    """Le tessere dei progetti su ⌘T (#5371): layout a stack, comandi, barra e tessere.js con node."""
    vc = repo / "shared/volta"
    mod = vc / "mods/arturo"
    lay = leggi(vc / "layouts/arturo.json")
    stack = []
    def cerca(n):
        if isinstance(n, dict):
            if n.get("id") == "lavoro":
                stack.append(n)
            for c in n.get("children", []):
                cerca(c)
    cerca(lay)
    if len(stack) != 1 or stack[0].get("type") != "stack" or stack[0].get("active") != "main":
        return "il layout non ha lo stack lavoro che mostra main all'avvio"
    figli = {c.get("id"): c for c in stack[0].get("children", [])}
    if list(figli) != ["main", "casa"] or figli["main"].get("content", {}).get("tab") != "active" \
            or figli["casa"].get("content") != {"mod": "arturo", "props": {"parte": "casa"}}:
        return f"lo stack lavoro non tiene il terminale e poi le tessere: {list(figli)}"
    bj = (mod / "barra.js").read_text(encoding="utf-8")
    for pezzo, perche in [
        ('else if (c === "casa") { run("layout.select", { stack: STACK, child: CASA }); setShared("arturo.casa.apri", Date.now()); }', "arturo.casa non mostra le tessere col campo vuoto"),
        ('else if (c === "casa-chiudi") terminale();', "arturo.casa-chiudi non torna al terminale"),
        ('else if (c === "casa" && senzaTessere(layout())) this.lungo("volta-nuova", cx, () => nuovaScheda());\n    else if (c === "casa") {', "con un layout senza tessere ⌘T non apre la sessione nuova (#5456)"),
        ("    this.volta.init(cx);\n", "manca la barra"),
        ("    terminale();\n    this.carica(cx);", "all'avvio lo stack non torna al terminale"),
        ('setShared("arturo.casa.progetti", tutti.map((p) => ({ chiave: p.chiave, titolo: p.titolo, frase: frase(p.stato, p) })));', "la barra non scrive i progetti delle tessere"),
    ]:
        if pezzo not in bj:
            return f"barra.js: {perche}"
    cs = (mod / "casa.js").read_text(encoding="utf-8")
    for pezzo, perche in [
        ('run(t.tipo === "nuova" ? "arturo.volta-nuova" : comandoConversazione(t.chiave));', "Invio non apre la tessera come la barra"),
        ('if (e.key === "escape") { terminale();', "Esc non torna al terminale"),
        ("readTextFile(`${appHome()}/immagini/elenco.json`)", "le tessere non leggono l'elenco delle immagini"),
        ("this.input.set_value(\"\");\n      this.input.focus();", "⌘T non riparte dal campo vuoto"),
        ('export const terminale = () => { if (!senzaTessere(layout())) run("layout.select"', "il ritorno al terminale manda layout.select anche a un layout senza tessere, con un avviso d'errore (#5456)"),
        ("child(`${tasti().tessere} poi Invio`)", "la tessera Nuova richiesta non scrive il tasto della macchina (#5456)"),
    ]:
        if pezzo not in cs:
            return f"casa.js: {perche}"
    init = cs[cs.find("  init(_p, cx) {"):cs.find("  leggiImmagini(cx) {")]
    if "terminale();" in init.replace("// Niente terminale() qui", ""):
        return "casa.js torna al terminale quando nasce, cioè subito dopo ⌘T"
    if "casa: Casa" not in (mod / "main.js").read_text(encoding="utf-8"):
        return "main.js non monta la parte casa"
    if '"benvenuto", "casa"]);' not in (mod / "main.js").read_text(encoding="utf-8"):
        return "la parte casa non riporta la sua misura: una nota sulle tessere non sa dove cade (#5456)"
    cm = (mod / "comuni.js").read_text(encoding="utf-8")
    if 'elenco: "⌘⇧E", tessere: "⌘T" }' not in cm or 'elenco: "Ctrl+Shift+I", tessere: "Ctrl+Shift+T" }' not in cm:
        return "tasti() non ha il tasto delle tessere per Mac e per Windows (#5456)"
    gd = (mod / "guida.js").read_text(encoding="utf-8")
    if "${tasti().tessere} mostra le tessere dei progetti" not in gd or "Altra conversazione" in gd:
        return "la guida non nomina le tessere, o parla ancora di Altra conversazione (#5456)"
    node = shutil.which("node")
    if not node:
        return None
    puro = casa / "puro"
    puro.mkdir()
    shutil.copyfile(mod / "tessere.js", puro / "tessere.mjs")
    shutil.copyfile(mod / "comandi.js", puro / "comandi.mjs")
    shutil.copyfile(mod / "nota.js", puro / "nota.mjs")
    shutil.copyfile(vc / "layouts/arturo.json", puro / "arturo.json")
    (puro / "prova.mjs").write_text(PROVA_TESSERE, encoding="utf-8")
    r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"tessere.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    righe = r.stdout.strip().splitlines()
    o, t = json.loads(righe[-2]), json.loads(righe[-1])
    if t["ha"] != [True, False, False] or t["senza"] != [False, True, False] or t["mostrate"] != [False, True, False]:
        return f"tessere.js non riconosce il layout con le tessere o le tessere mostrate: {t['ha']} {t['senza']} {t['mostrate']}"
    if t["regione"] != ["main", "tessere", "casa"]:
        return f"una nota sulle tessere mostrate va alla sessione: {t['regione']}"
    if (t["sotto"] or {}).get("blocco") != "tessere" or (t["sotto"] or {}).get("nome") != "Tessera del progetto · Tessere dei progetti":
        return f"elementoSotto() non riconosce una tessera: {t['sotto']}"
    if t["nomi"] != ["Elenco delle tessere", "Tessera Nuova richiesta", "Tessera del progetto", None]:
        return f"nomi degli elementi delle tessere sbagliati: {t['nomi']}"
    if o["vuoto"] != ["nuova", "sei-ore", "celestiale", "arturo", "radio-lago", "solaris"] or o["nessuno"] != ["nuova"]:
        return f"le tessere senza filtro non sono Nuova richiesta e poi i progetti in ordine: {o['vuoto']} {o['nessuno']}"
    if o["ra"] != ["radio-lago"] or o["dentro"] != ["celestiale"] or o["s"] != ["sei-ore", "solaris", "celestiale"]:
        return f"il filtro sbaglia (prima chi comincia così, poi chi lo contiene, senza Nuova richiesta): {o['ra']} {o['dentro']} {o['s']}"
    if o["col"] != [1, 1, 1, 1, 2]:
        return f"colonne() sbaglia quante tessere stanno in una riga: {o['col']}"
    if o["passi"] != [1, 9, 0, 5, 8, 9, 2, 2, 3, 0]:
        return f"le frecce sbagliano tessera (o girano oltre il bordo): {o['passi']}"
    if o["iniziali"] != ["SO", "CE", "DM", "?", "ÈB"]:
        return f"iniziali() sbaglia: {o['iniziali']}"
    if o["tinta"][0] != o["tinta"][1] or o["tinta"][0] == o["tinta"][2] or not re.fullmatch(r"#[0-9a-f]{6}", o["tinta"][0]):
        return f"tinta() non è stabile per slug o non è un colore del tema: {o['tinta']}"
    if o["img"] != ["immagini/arturo.webp", None, None]:
        return f"immagine() mostra un'immagine che non c'è: {o['img']}"
    if o["nuova"]["tipo"] != "nuova" or o["stack"] != ["lavoro", "main", "casa"]:
        return f"tessere.js: prima tessera o nomi dello stack: {o['nuova']} {o['stack']}"
    if o["comandi"] != [{"verbo": "casa", "arg": None, "lungo": False}, {"verbo": "casa-chiudi", "arg": None, "lungo": False}]:
        return f"instrada() non conosce arturo.casa e arturo.casa-chiudi: {o['comandi']}"
    return None


PROVA_CERCA = r"""
import { cerca, impostaProgetti, comandoNuova, decodifica, VIVE_SENZA_TESTO } from "./sessioni.mjs";
impostaProgetti({ "herdr-arturo": { chiave: "herdr-arturo", titolo: "Volta" }, volta: { chiave: "herdr-arturo", titolo: "Volta" } });
const S = [
  { sessionId: "a", id: "a1", titolo: "Rinomina del repo", progetto: "herdr-arturo", tipo: "background", ultimo: "2026-11-12T10:00:00Z" },
  { sessionId: "b", id: "b1", titolo: "Volta vecchia", progetto: "x", tipo: "background", chiusa: true, ultimo: "2026-11-12T12:00:00Z" },
  { sessionId: "c", id: "c1", titolo: "Post sul fiume", progetto: "post-office", tipo: "background", ultimo: "2026-11-12T11:00:00Z" },
  { sessionId: "d", id: "d1", titolo: "Il post di ieri", progetto: "sei-ore", tipo: "background", ultimo: "2026-11-12T11:30:00Z" },
];
const P = ["herdr-arturo", "post-office", "sei-ore"];
const v = (r) => r.map((x) => x.tipo === "sessione" ? "s:" + x.s.sessionId : x.tipo === "progetto" ? "p:" + x.nome : "n:" + x.testo);
const molte = Array.from({ length: 9 }, (_, i) => ({ sessionId: "m" + i, id: "m" + i, titolo: "Sessione " + i, tipo: "background", ultimo: "2026-11-1" + (i % 9) + "T10:00:00Z" }));
const hex = comandoNuova("  ciao è 😀  ").slice("arturo.nuova-".length);
console.log(JSON.stringify({
  vuoto: v(cerca(S, P, "")), volta: v(cerca(S, P, "volta")), post: v(cerca(S, P, "pòst")), niente: v(cerca(S, P, "zzz")),
  tetto: cerca(molte, P, "").length, vive: cerca(molte, [], "").length, max: VIVE_SENZA_TESTO, corto: cerca(molte, P, "sessione", 4).length,
  testo: decodifica(hex), hex: /^(?:[0-9a-f]{4})+$/.test(hex),
}));
"""


def hz98(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    aj = (mod / "apri.js").read_text(encoding="utf-8")
    for pezzo, motivo in (("const [lista, sessioni] = await Promise.all([nomiProgetti(), sessioniVolta()]);", "non legge le sessioni di Volta"),
                          ("return cerca(this.sessioni, this.lista ?? [], this.filtro);", "non usa cerca()"),
                          ("impostaProgetti(shared(\"arturo.progetti\"));", "non conosce i titoli dei progetti")):
        if pezzo not in aj:
            return f"apri.js {motivo}"
    if "export async function sessioniVolta()" not in (mod / "dati.js").read_text(encoding="utf-8"):
        return "dati.js non legge le sessioni di Volta per la ricerca"
    node = shutil.which("node")
    if not node:
        return None
    puro = casa / "puro"
    puro.mkdir()
    shutil.copyfile(mod / "sessioni.js", puro / "sessioni.mjs")
    (puro / "prova.mjs").write_text(PROVA_CERCA, encoding="utf-8")
    r = subprocess.run([node, str(puro / "prova.mjs")], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["vuoto"] != ["s:d", "s:c", "s:a", "p:herdr-arturo", "p:post-office", "p:sei-ore"]:
        return f"cerca() senza testo: {d['vuoto']}"
    if d["volta"] != ["s:a", "p:herdr-arturo", "s:b", "n:volta"]:
        return f"cerca() non trova dal titolo del progetto o non tiene le chiuse in fondo: {d['volta']}"
    if d["post"] != ["s:c", "p:post-office", "s:d", "n:pòst"]:
        return f"cerca() non mette prima chi comincia col testo, o non ignora gli accenti: {d['post']}"
    if d["niente"] != ["n:zzz"]:
        return f"cerca() senza risultati non propone Nuova richiesta: {d['niente']}"
    if d["vive"] != d["max"] or d["tetto"] != 8 or d["corto"] != 4:
        return f"cerca() non tiene i tetti: {d['vive']} vive (max {d['max']}), {d['tetto']} righe, {d['corto']} con 4"
    if d["testo"] != "ciao è 😀" or not d["hex"]:
        return f"comandoNuova() non torna intero: {d['testo']!r}"
    return None


def hz99(repo: Path, casa: Path) -> str | None:
    vc = repo / "shared/volta"
    mac = leggi(vc / "keys.json").get("global", {})
    win = leggi(vc / "keys-ctrl.json").get("global", {})
    if mac.get("cmd-k") != "arturo.apri" or mac.get("cmd-o") != "arturo.apri":
        return f"⌘K e ⌘O non aprono la stessa ricerca: {mac.get('cmd-k')}, {mac.get('cmd-o')}"
    if win.get("ctrl-shift-a") != "arturo.apri":
        return f"su Windows Ctrl+Shift+A non apre Cerca: {win}"
    mod = vc / "mods/arturo"
    if "import { rigaMod, decodifica } from \"./sessioni.js\";" not in (mod / "barra.js").read_text(encoding="utf-8"):
        return "barra.js non decodifica il testo di Nuova richiesta"
    cj = (mod / "comuni.js").read_text(encoding="utf-8")
    if '{ apri: "⌘K", giro: "⌘↓ ⌘↑",' not in cj or 'giro: "Ctrl+↓ Ctrl+↑",' not in cj:
        return "tasti() di comuni.js non dice ⌘K e il giro"
    return None


def hz100(repo: Path, casa: Path) -> str | None:
    for sistema, serie, mio, nuova in (("mac-arm", "keys-herdr-macos.json", "keys.json", "cmd-t"), ("windows", "keys-herdr.json", "keys-ctrl.json", "ctrl-shift-t")):
        dove = casa / sistema
        dove.mkdir()
        extra = {"HERDR_APP_HOME": str(dove / "app")} if sistema == "windows" else {}
        r = installa(repo, dove, sistema, extra)
        if r.returncode != 0:
            return f"installazione {sistema} fallita: {(r.stdout + r.stderr)[-200:]}"
        avuti = leggi(dove / "app" / "keys.json")
        base = leggi(repo / "shared/volta" / serie)
        arturo = leggi(repo / "shared/volta" / mio)["global"]
        for sez, voci in base.items():
            for k, v in voci.items():
                atteso = arturo.get(k, v) if sez == "global" else v
                if avuti.get(sez, {}).get(k) != atteso:
                    return f"{sistema}: senza keys.json manca il tasto di serie {sez}.{k} ({avuti.get(sez, {}).get(k)}, atteso {atteso})"
        if any(avuti["global"].get(k) != v for k, v in arturo.items()):
            return f"{sistema}: i tasti di Arturo non stanno sopra quelli di serie"
        if avuti["global"].get(nuova) != "arturo.casa":
            return f"{sistema}: ⌘T non porta alle tessere dei progetti"
    return None


Date_T = 1794484800000  # 2026-11-12T12:00:00Z, lo stesso T di PROVA_AUTO

PROVA_OCCUPATE = r"""
import { schedeAgganciate, schedeDi } from "./dati.mjs";
import * as S from "./sessioni.mjs";
import { setShared } from "./herdr.mjs";
const { sessioneDi, occupanti } = S;  // senza occupanti (codice di prima) la prova gira e dice cosa sbaglia
const fuori = { id: "a8ee6d5e", sessionId: "791f271d", tipo: "background", host: "amaltea", macchina: "Amaltea", questa: false };
const qui = { id: "30ffae9e", sessionId: "30ffae9e-b5ca", tipo: "interattiva", questa: true, terminale: "t18", progetto: "p" };
const sessioni = [fuori, qui];
const t18 = { address: "t18", argv: ["pwsh.exe", "-NoExit", "-Command", String.raw`& 'C:\x\ssh.exe' '-t' 'amaltea' 'claude' 'attach' 'a8ee6d5e'`],
              labels: { "arturo.sessione": "a8ee6d5e" } };
const prima = { di: sessioneDi(t18, sessioni)?.id ?? null, agganciate: Object.keys(schedeAgganciate(sessioni)) };
const occupate = typeof occupanti === "function" ? Object.fromEntries(Object.entries(occupanti(sessioni)).map(([a, s]) => [a, s.id])) : {};
setShared("arturo.volta.dove", { qui: "Torre", schede: {}, occupate });
console.log(JSON.stringify({ ...prima, schedeDi: schedeDi(fuori).map((x) => x.address) }));
"""


def hz95(repo: Path, casa: Path) -> str | None:
    node = shutil.which("node")
    if not node:
        return None
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (repo / "shared/volta/mods/arturo/dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_OCCUPATE, encoding="utf-8")
    nascita = ["pwsh.exe", "-NoExit", "-Command", r"& 'C:\x\ssh.exe' '-t' 'amaltea' 'claude' 'attach' 'a8ee6d5e'"]
    herdr = {"spaces": [], "panes": [{"terminal": "t18", "tab": "tb1"}],
             "terminals": [{"address": "t18", "argv": nascita, "labels": {"arturo.sessione": "a8ee6d5e"}, "state": "live"}]}
    e = {**os.environ, "HZ_APP": str(casa), "HZ_CASA": str(casa), "HZ_HERDR": json.dumps(herdr), "HZ_SHARED": "{}"}
    r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", env=e, timeout=60)
    if r.returncode != 0:
        return f"la prova non gira: {(r.stderr or r.stdout).strip()[:200]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["di"] != "30ffae9e":
        return f"la scheda mostra la sessione con cui è nata, non quella che ci gira: {g['di']}"
    if g["agganciate"]:
        return f"una scheda occupata da un'interattiva conta ancora come aggancio: {g['agganciate']}"
    if g["schedeDi"]:
        return f"con occupate in shared la sessione di nascita trova ancora la scheda: {g['schedeDi']}"
    # la scheda della testata (volta 4e4eada, ea206f8): l'id dell'aggancio si legge anche da pwsh -Command
    # "<riga>" e da sh -c "... attach id"; una scheda occupata è dell'interattiva che ci gira
    (m / "scheda.mjs").write_text(PROVA_SCHEDA, encoding="utf-8")
    herdr = {"spaces": [], "panes": [{"terminal": "t19", "tab": "tbW"}, {"terminal": "t5", "tab": "tbM"},
                                     {"terminal": "t6", "tab": "tbS"}, {"terminal": "t7", "tab": "tbN"}],
             "terminals": [
                 {"address": "t19", "argv": ["pwsh.exe", "-NoExit", "-Command", r"& 'C:\Windows\System32\OpenSSH\ssh.exe' '-t' 'amaltea' '/Users/u/.local/bin/claude' 'attach' '21b6fac2'"]},
                 {"address": "t5", "argv": ["/bin/zsh", "-lic", '"$@"; exec "$0" -li', "/bin/zsh", "claude", "attach", "a1b2c3d4"]},
                 {"address": "t6", "argv": ["sh", "-c", "while :; do ssh -t torre claude attach a1b2c3d4; sleep 2; done"]},
                 {"address": "t7", "argv": ["pwsh.exe", "-NoExit", "-Command", "$global:__hc_prompt = $function:prompt"]}]}
    e = {**os.environ, "HZ_APP": str(casa), "HZ_CASA": str(casa), "HZ_HERDR": json.dumps(herdr), "HZ_SHARED": "{}"}
    r = subprocess.run([node, str(m / "scheda.mjs")], capture_output=True, text=True, encoding="utf-8", env=e, timeout=60)
    if r.returncode != 0:
        return f"la prova della testata non gira: {(r.stderr or r.stdout).strip()[:200]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    atteso = {"windows": "21b6fac2", "windowsStato": "working", "mac": "a1b2c3d4", "shell": "a1b2c3d4", "nessuna": None, "occupata": "30ffae9e"}
    sbagliati = {k: g.get(k) for k, v in atteso.items() if g.get(k) != v}
    if sbagliati:
        return f"la testata non trova la sessione della scheda aperta (attesi {atteso}): {sbagliati}"
    return None


PROVA_SCHEDA = r"""
import { schedaAgganciata, statoSpazio } from "./dati.mjs";
import { setShared } from "./herdr.mjs";
setShared("arturo.volta.stati", { "21b6fac2": { stato: "lavora", host: "amaltea" }, "a1b2c3d4": { stato: "aspetta", host: "qui" } });
const spazio = (tab) => ({ tabs: [{ id: tab, active: true }] });
const esito = {
  windows: schedaAgganciata(spazio("tbW"))?.id ?? null, windowsStato: statoSpazio(spazio("tbW")),
  mac: schedaAgganciata(spazio("tbM"))?.id ?? null, shell: schedaAgganciata(spazio("tbS"))?.id ?? null,
  nessuna: schedaAgganciata(spazio("tbN"))?.id ?? null,
};
setShared("arturo.volta.dove", { occupate: { t19: "30ffae9e" } });
esito.occupata = schedaAgganciata(spazio("tbW"))?.id ?? null;
console.log(JSON.stringify(esito));
"""


PROVA_IMPORT_NOTE = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import volta_note, volta_sonda
nomi = ("errore_hc", "hc", "leggi_json", "macchine", "non_parte", "scrivi_atomico")
print(json.dumps({"mancano": [n for n in nomi if not callable(getattr(volta_sonda, n, None))],
                  "sincronizza": callable(getattr(volta_note, "sincronizza", None))}))
'''


def hz97(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    r = subprocess.run([sys.executable, "-I", "-c", PROVA_IMPORT_NOTE, str(mod)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(casa), env={**os.environ, "CLAUDE_CONFIG_DIR": str(casa)}, timeout=60)
    if r.returncode != 0:
        return f"volta_note.py non parte accanto a volta_sonda.py: {(r.stderr or r.stdout).strip()[-200:]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["mancano"] or not g["sincronizza"]:
        return f"volta_sonda.py non dà più a volta_note.py {g['mancano'] or 'sincronizza'}"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ("this.noteScript = await esiste(`${appHome()}/mods/arturo/volta_note.py`);",
                  '"sincronizza", "--scrivi", `${cacheVolta("volta-note")}/stato.json`]',
                  "      cx.notify();\n      this.sincronizzaNote(cx);"):
        if pezzo not in vj:
            return f"volta.js non lancia più il giro delle note dopo l'elenco: manca {pezzo[:60]!r}"
    return None



PROVA_ACCESA = r"""
const n = await import(%s);
const c = await import(%s);
const l = [{ host: "qui", id: "a", sessionId: "A", stato: "ferma", tipo: "background" },
  { host: "amaltea", id: "a", sessionId: "A", stato: "aspetta", tipo: "background" },
  { host: "torre", id: "b", sessionId: "B", stato: "ferma", tipo: "interattiva", terminale: "t13" },
  { host: "torre", id: "d", sessionId: "D", stato: "ferma", tipo: "background" },
  { host: "qui", id: "e", sessionId: "E", stato: "ferma" }, { host: "amaltea", id: "e", sessionId: "E", stato: "ferma" }];
const g = { ids: ["a", "b"], ultimo: "b", quando: 1000 };
console.log(JSON.stringify({
  corrente: [n.corrente(g, "a", 1500), n.corrente(g, "a", 1001 + n.GIRO_MS), n.corrente(null, "a", 5), n.corrente(null, null, 5)],
  davanti: [n.sessioneDavanti({ address: "torre/t13", labels: { "arturo.sessione": "d" } }, l)?.id ?? null,
    n.sessioneDavanti({ address: "amaltea/t13" }, l), n.sessioneDavanti(null, l)],
  una: n.unaPerConversazione(l).map((s) => s.host + "/" + s.id),
  conversazione: c.instrada("conversazione-volta"),
  sposta: [c.instrada("volta-sposta-amaltea-936135fc"), c.instrada("volta-sposta-studio-ab12cd34").arg, c.instrada("volta-936135fc").verbo],
}));
"""


def hz101(repo: Path, casa: Path) -> str | None:
    """La riga accesa dell'elenco e il comando di Sposta su."""
    mod = repo / "shared/volta/mods/arturo"
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo in ("this.acceso = corrente(this.giroSt, davanti ? chiave(davanti) : null, Date.now());",
                  "const acceso = this.acceso === k;", 'else if (c === "volta-sposta") this.volta.spostaId(arg.macchina, arg.id, cx);'):
        if pezzo not in volta + (mod / "barra.js").read_text(encoding="utf-8"):
            return f"volta.js o barra.js non hanno più: {pezzo[:70]}"
    if "comandoConversazione(t.chiave)" not in (mod / "casa.js").read_text(encoding="utf-8") or \
            'else if (c === "conversazione") { if (arg) this.lungo(c, cx, () => conversazione(arg)); }' not in (mod / "barra.js").read_text(encoding="utf-8"):
        return "la tessera di un progetto su ⌘T non fa più nascere una conversazione nuova (comandoConversazione, conversazione())"
    testata = (mod / "testata.js").read_text(encoding="utf-8")
    if 'bottone("sposta", ICONA_SPOSTA' not in testata or "sposta: SceltaSposta" not in (mod / "main.js").read_text(encoding="utf-8"):
        return "la testata ha perso il pulsante Sposta su, o main.js il suo popup"
    node = shutil.which("node")
    if not node:
        return None
    for nome in ("sessioni", "comandi"):
        shutil.copyfile(mod / f"{nome}.js", casa / f"{nome}.mjs")
    r = subprocess.run([node, "--input-type=module", "-e",
                        PROVA_ACCESA % (json.dumps((casa / "sessioni.mjs").as_uri()), json.dumps((casa / "comandi.mjs").as_uri()))],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["corrente"] != ["b", "a", "a", None]:
        return f"corrente() non segue il giro dentro la raffica, o non torna alla scheda dopo: {g['corrente']}"
    if g["davanti"] != ["b", None, None]:
        return f"sessioneDavanti() non riconosce chi gira nel terminale di un'altra macchina: {g['davanti']}"
    if g["una"] != ["amaltea/a", "torre/b", "torre/d", "qui/e", "amaltea/e"]:
        return f"unaPerConversazione() non toglie la copia ferma di una sessione spostata: {g['una']}"
    if g["sposta"] != [{"verbo": "volta-sposta", "arg": {"macchina": "amaltea", "id": "936135fc"}, "lungo": False},
                       {"macchina": "studio", "id": "ab12cd34"}, "volta"]:
        return f"instrada() non legge volta-sposta-<macchina>-<id>: {g['sposta']}"
    if g["conversazione"] != {"verbo": "conversazione", "arg": "volta", "lungo": True}:
        return f"instrada() non legge conversazione-<slug>: {g['conversazione']}"
    return None


# Due macchine finte nella stessa casa: ognuna con la sua cartella di Herdr (base dei progetti) e la sua
# cartella di Claude. Gli script di volta_sposta.py girano come girano con hc exec: python -c CODICE ARG.
PROVA_SPOSTA = r'''
import base64, io, json, os, re, subprocess, sys, tarfile
mod, casa = sys.argv[1], sys.argv[2]
sys.path.insert(0, mod)
import volta_sposta as vs
def g(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)
remoto = os.path.join(casa, "remoto.git")
g(casa, "init", "-q", "--bare", remoto)
basi = {"da": os.path.join(casa, "da", "progetti"), "a": os.path.join(casa, "a", "progetti")}
for lato, base in basi.items():
    os.makedirs(base)
    os.makedirs(os.path.join(casa, lato, "herdr"))
    with open(os.path.join(casa, lato, "herdr", "arturo.json"), "w") as fh:
        json.dump({"base": base}, fh)
progetto = os.path.join(basi["da"], "prova")
os.makedirs(progetto)
g(progetto, "init", "-q", "-b", "main")
g(progetto, "config", "user.email", "banco@prova")
g(progetto, "config", "user.name", "banco")
open(os.path.join(progetto, "x.txt"), "w").write("uno")
g(progetto, "add", "x.txt")
g(progetto, "commit", "-qm", "uno")
g(progetto, "remote", "add", "origin", remoto)
g(progetto, "push", "-q", "-u", "origin", "main")
sid = "1234abcd-0000-4000-8000-000000000000"
cartella_claude = os.path.join(casa, "da", "claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", progetto))
os.makedirs(os.path.join(cartella_claude, sid))
open(os.path.join(cartella_claude, sid + ".jsonl"), "w").write(json.dumps({"cwd": progetto}) + "\n")
open(os.path.join(cartella_claude, sid, "nota.txt"), "w").write("dentro")
def lancia(lato, codice, dati, entrata=None):
    env = {**os.environ, "HERDR_APP_HOME": os.path.join(casa, lato, "herdr"), "CLAUDE_CONFIG_DIR": os.path.join(casa, lato, "claude")}
    arg = base64.b64encode(json.dumps(dati).encode()).decode()
    r = subprocess.run([sys.executable, "-c", codice, arg], capture_output=True, text=True, input=entrata or "", env=env, timeout=120)
    return vs.vs.leggi_json(r.stdout) if r.stdout.strip() else {"errore": r.stderr.strip()[-200:]}
out = {}
letto = lancia("da", vs.LEGGI, {"cartella": progetto, "sid": sid})
out["letto"] = {k: letto.get(k) for k in ("rel", "byte", "errore")}
out["pulito"] = vs.controlla_git(letto.get("git"))
open(os.path.join(progetto, "y.txt"), "w").write("due")
out["sporco"] = vs.controlla_git(lancia("da", vs.LEGGI, {"cartella": progetto, "sid": sid}).get("git"))
g(progetto, "add", "y.txt")
g(progetto, "commit", "-qm", "due")
out["non_spinto"] = vs.controlla_git(lancia("da", vs.LEGGI, {"cartella": progetto, "sid": sid}).get("git"))
g(progetto, "push", "-q")
g(progetto, "checkout", "-q", "--detach")
out["staccata"] = vs.controlla_git(lancia("da", vs.LEGGI, {"cartella": progetto, "sid": sid}).get("git"))
g(progetto, "checkout", "-q", "main")
letto = lancia("da", vs.LEGGI, {"cartella": progetto, "sid": sid})
if letto.get("errore"):
    print(json.dumps({"errore_letto": letto["errore"]}))
    raise SystemExit
pronto = lancia("a", vs.PREPARA, {"rel": letto["rel"], "git": letto["git"], "nome": "a"})
out["pronto"] = {"cartella": pronto.get("cartella"), "progetti": pronto.get("progetti"), "errore": pronto.get("errore"),
                 "y": os.path.exists(os.path.join(basi["a"], "prova", "y.txt"))}
pacco = lancia("da", vs.PACCO, {"trascrizione": letto["trascrizione"], "sid": sid})
s1 = lancia("a", vs.SCARICA, {"sid": sid, "progetti": pronto["progetti"]}, pacco["pacco"])
s2 = lancia("a", vs.SCARICA, {"sid": sid, "progetti": pronto["progetti"]}, pacco["pacco"])
out["scarica"] = [s1.get("byte") == pacco["byte"], s2.get("byte") == pacco["byte"],
                  os.path.exists(os.path.join(pronto["progetti"], sid, "nota.txt")),
                  len([f for f in os.listdir(pronto["progetti"]) if ".prima-" in f])]
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as t:
    info = tarfile.TarInfo("../fuori.txt"); info.size = 2; t.addfile(info, io.BytesIO(b"no"))
cattivo = lancia("a", vs.SCARICA, {"sid": sid, "progetti": pronto["progetti"]}, base64.b64encode(buf.getvalue()).decode())
out["cattivo"] = [bool(cattivo.get("errore")), os.path.exists(os.path.join(os.path.dirname(pronto["progetti"]), "fuori.txt"))]
sid2 = "5678abcd-0000-4000-8000-000000000000"
fuori_claude = os.path.join(casa, "da", "claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", casa))
os.makedirs(fuori_claude)
open(os.path.join(fuori_claude, sid2 + ".jsonl"), "w").write(json.dumps({"cwd": casa}) + "\n")
fuori = lancia("da", vs.LEGGI, {"cartella": casa, "sid": sid2})
out["fuori"] = bool(fuori.get("errore"))
lancia("a", vs.SEGNA, {"sid": sid, "progetto": "prova"})
scheda = json.load(open(os.path.join(casa, "a", "claude", "cache", "scheda", sid + ".json")))
out["segna"] = [scheda.get("progetto"), scheda.get("fonte"), "inizio" in scheda]
print(json.dumps(out))
'''


def hz102(repo: Path, casa: Path) -> str | None:
    """Sposta su: volta_sposta.py legge git, prepara l'altra macchina e porta la trascrizione."""
    mod = repo / "shared/volta/mods/arturo"
    if 'if argv and argv[0] == "sposta":' not in (mod / "volta_sonda.py").read_text(encoding="utf-8"):
        return "volta_sonda.py non passa più il verbo sposta a volta_sposta.py"
    if not shutil.which("git"):
        return None
    r = subprocess.run([sys.executable, "-I", "-c", PROVA_SPOSTA, str(mod), str(casa)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(casa), timeout=240)
    if r.returncode != 0:
        return f"volta_sposta.py non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g.get("errore_letto"):
        return f"LEGGI non trova la cartella della trascrizione: {g['errore_letto'][:120]}"
    if g["letto"]["errore"] or g["letto"]["rel"] != "prova" or g["pulito"] is not None:
        return f"LEGGI non legge una cartella pulita e spinta: {g['letto']}, {g['pulito']}"
    # File non salvati e commit non spinti viaggiano con la sessione (#5500); una HEAD staccata la ferma.
    if g["sporco"] is not None or g["non_spinto"] is not None:
        return f"lo spostamento si ferma davanti a file non salvati o commit non spinti, che viaggiano: {g['sporco']} / {g['non_spinto']}"
    if "HEAD staccata" not in str(g["staccata"]):
        return f"lo spostamento non si ferma su una HEAD staccata: {g['staccata']}"
    p = g["pronto"]
    if p["errore"] or not p["y"] or not str(p["progetti"]).endswith(re.sub(r"[^A-Za-z0-9]", "-", str(p["cartella"]))):
        return f"PREPARA non porta il repository allo stesso commit, o sbaglia la cartella di Claude: {p}"
    if g["scarica"] != [True, True, True, 2]:
        return f"la trascrizione non arriva intera, o una copia di prima non resta da parte: {g['scarica']}"
    if g["cattivo"] != [True, False]:
        return f"SCARICA apre un pacco con un nome fuori dalla cartella: {g['cattivo']}"
    if not g["fuori"]:
        return "LEGGI accetta una cartella fuori dalla base dei progetti"
    if g["segna"] != ["prova", "teletrasporto", False]:
        return f"SEGNA non porta il progetto come teletrasporto, o lascia il segno di /inizio: {g['segna']}"
    return None


PROVA_TRASCINO = r"""
const m = await import(%s);
m.impostaProgetti({ "due-mondi": { chiave: "due-mondi", nome: "Due Mondi" } });
const s = { sessionId: "a-lungo", progetto: "due-mondi" };
const t = { s, mosso: true };
console.log(JSON.stringify({
  soglia: m.MOSSA_PX,
  mosso: [m.mosso({ x: 0, y: 0 }, { x: 3, y: 4 }), m.mosso({ x: 10, y: 10 }, { x: 10, y: 16 }), m.mosso(null, { x: 9, y: 9 })],
  arrivo: [m.arrivoTrascino(t, { chiave: "sito-uf" }, "progetto"), m.arrivoTrascino(t, { chiave: "Post Office" }, "progetto"),
           m.arrivoTrascino(t, { chiave: "due-mondi" }, "progetto"), m.arrivoTrascino(t, { chiave: "sito-uf" }, "macchina"),
           m.arrivoTrascino(t, { chiave: "" }, "progetto"), m.arrivoTrascino({ s, mosso: false }, { chiave: "sito-uf" }, "progetto"),
           m.arrivoTrascino({ s: { ...s, vecchia: true }, mosso: true }, { chiave: "sito-uf" }, "progetto"), m.arrivoTrascino(null, { chiave: "x" }, "progetto")],
}));
"""


def hz103(repo: Path, casa: Path) -> str | None:
    """Una sessione si trascina su un altro progetto, nella vista per progetto."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, motivo in (
            ('.on_mouse_down("left", (e) => { if (modo === "progetto") this.trascino = { s, da: e.position, mosso: false, sopra: null }; })',
             "la pressione sulla riga non comincia il trascinamento, o lo comincia anche nella vista per macchina"),
            ("if (this.trascino && !this.trascino.mosso && mosso(this.trascino.da, e.position)) { this.trascino.mosso = true; cx.notify(); }",
             "il movimento sull'elenco non fa partire il trascinamento"),
            ('.on_mouse_up("left", (_e, cx) => { if (this.trascino) this.finisciTrascino(null, modo, cx); })', "un rilascio fuori da un gruppo non chiude il trascinamento"),
            ("this.finisciTrascino(g, modo, cx);\n        cx.stop_propagation();", "il rilascio su un gruppo non sposta la sessione"),
            ('if (arrivo) this.cambia(tr.s, "progetto", arrivo, cx);', "il trascinamento non passa da cambia(), come Cambia progetto"),
            ("if (this.trascino?.mosso || Date.now() - this.trascinata < 500) return;", "il rilascio dopo un trascinamento apre la sessione"),
            ("Lascia qui per spostarla in ${g.titolo}", "il gruppo d'arrivo non dice cosa succede se lasci la sessione")):
        if pezzo not in vj:
            return f"volta.js: {motivo}"
    node = shutil.which("node")
    if not node:
        return None
    copia = casa / "sessioni.mjs"
    shutil.copyfile(mod / "sessioni.js", copia)
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_TRASCINO % json.dumps(copia.as_uri())], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["soglia"] != 6 or d["mosso"] != [False, True, False]:
        return f"mosso() sbaglia la soglia fra clic e trascinamento: {d['soglia']}, {d['mosso']}"
    if d["arrivo"] != ["sito-uf", "post-office", None, None, None, None, None, None]:
        return f"arrivoTrascino() sbaglia il progetto d'arrivo: {d['arrivo']}"
    return None


PROVA_SPOSTA_TUTTO = r"""
const n = await import(%s);
const c = await import(%s);
const r = (o) => ({ tipo: "background", stato: "ferma", host: "qui", macchina: "Torre", ...o });
const l = [r({ id: "a1", sessionId: "s1" }), r({ id: "a2", sessionId: "s2", stato: "lavora" }),
  r({ id: "a3", sessionId: "s3", host: "studio", macchina: "Studio" }), r({ id: "a4", sessionId: "s4", tipo: "interattiva" }),
  r({ id: "a5", sessionId: "s5", chiusa: true }), r({ id: "a6", sessionId: "s6", stato: "errore" }),
  r({ id: "a7", sessionId: "s7", vecchia: true })];
console.log(JSON.stringify({
  suStudio: n.spostabili(l, "studio").map((s) => s.id), suQui: n.spostabili(l, "qui").map((s) => s.id),
  conto: [n.contoTutto(l, "studio"), n.contoTutto(l, "qui"), n.contoTutto([], "qui")],
  lavora: n.nonSiSposta(l[1]), interattiva: Boolean(n.nonSiSposta(l[3])),
  menu: [n.menu(l[0]).some((v) => v.verbo === "sposta"), n.menu(l[3]).some((v) => v.verbo === "sposta")],
  per: n.perSposta(r({ id: "a1", sessionId: "s1", nome: "Prova", risposta: "lunga" })),
  tutto: [c.instrada("volta-spostatutto-torre-due"), c.instrada("volta-sposta-torre-due-a1b2").arg],
}));
"""

# volta_sposta.py con gli script finti: lo stato del turno a ogni lettura di TROVA, e cosa ha chiamato.
PROVA_TURNO = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import volta_sposta as v
esiti = {}
# viva: claude stop fallisce e la sessione ha ancora un processo; ferma: fallisce perché è già ferma (#5574)
for nome, stati, stop, pid in (("subito", ["busy"], {}, None), ("dopo", ["idle", "busy"], {}, None),
                               ("libera", ["idle", "idle", "idle"], {}, None),
                               ("viva", ["idle", "idle", "idle"], {"errore": "rc 1"}, 4242),
                               ("ferma", ["idle", "idle", "idle"], {"errore": "No job matching"}, None)):
    giro, chiamate = iter(stati), []
    def finto(macchina, codice, dati, entrata=None, timeout=0):
        if codice is v.TROVA:
            chiamate.append("trova")
            return {"ok": True, "id": "abcd1234", "claude": "claude", "stato": next(giro, "idle"), "pid": pid}
        if codice is v.LEGGI:
            chiamate.append("leggi")
            return {"rel": "p", "trascrizione": "t", "git": None}
        if codice is v.PREPARA:
            chiamate.append("prepara")
            return {"cartella": "/x", "progetti": "/y"}
        chiamate.append("altro")
        return {"errore": "fine della prova"}
    v.esegui = finto
    v.vs.azione = lambda m, verbo, i, stop=stop: chiamate.append(verbo) or dict(stop)
    v.vs.nasci = lambda *a, **k: {"errore": "fine della prova"}
    r = v.sposta("qui", "studio", "abcd1234", "abcd1234-0000", "/x")
    esiti[nome] = {"lavora": r.get("lavora") is True, "chiamate": chiamate, "errore": r.get("errore")}
print(json.dumps(esiti))
'''


def hz104(repo: Path, casa: Path) -> str | None:
    """Sposta su dal menu e Sposta tutto su, a turno finito."""
    mod = repo / "shared/volta/mods/arturo"
    volta = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, perche in (("      this.passiCongedo(cx);\n      this.giraCoda(cx);", "il giro dell'elenco non fa partire la coda di Sposta"),
                          ("if (aFineTurno(s) || v.dopo > ora) continue;", "la coda sposta una sessione a metà turno"),
                          ("if (r.lavora) this.codaSposta[k] = { ...v, dopo: Date.now() + OGNI };", "un turno appena partito toglie la sessione dalla coda"),
                          ('if (verbo === "sposta") return apriSposta(perSposta(this.vistaId(id) ?? s));', "Sposta su… del menu non apre il popup delle macchine")):
        if pezzo not in volta:
            return f"volta.js: {perche}"
    barra = (mod / "barra.js").read_text(encoding="utf-8")
    if 'else if (c === "volta-spostatutto") this.volta.spostaTutto(arg, cx);' not in barra or "const fila = [dove, tutto].filter(Boolean);" not in barra or ".children(fila))))" not in barra:
        return "la barra non ha Sposta tutto su… sotto Nasce su, o non esegue il suo comando"
    if 'spostatutto: SceltaSpostaTutto' not in (mod / "main.js").read_text(encoding="utf-8"):
        return "main.js non ha il popup di Sposta tutto su"
    if 'v.verbo !== "sposta" || destinazioni(s, vociMacchina()).length > 0' not in (mod / "menusessione.js").read_text(encoding="utf-8"):
        return "il menu mostra Sposta su… anche senza un'altra macchina"
    r = subprocess.run([sys.executable, "-I", "-c", PROVA_TURNO, str(mod)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if r.returncode != 0:
        return f"volta_sposta.py non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    t = json.loads(r.stdout.strip().splitlines()[-1])
    if {k: t["subito"][k] for k in ("lavora", "chiamate")} != {"lavora": True, "chiamate": ["trova"]}:
        return f"una sessione che lavora non si ferma prima di leggere: {t['subito']}"
    if not t["dopo"]["lavora"] or "stop" in t["dopo"]["chiamate"]:
        return f"un turno partito mentre la cartella si prepara viene interrotto: {t['dopo']}"
    if t["libera"]["lavora"] or "stop" not in t["libera"]["chiamate"]:
        return f"una sessione ferma non si sposta: {t['libera']}"
    viva = t["viva"]
    if viva["chiamate"][-2:] != ["stop", "trova"] or "altro" in viva["chiamate"] or "non ferma" not in (viva["errore"] or ""):
        return f"Sposta va avanti anche se claude stop lascia viva la sessione di partenza: {viva}"
    if "altro" not in t["ferma"]["chiamate"]:
        return f"Sposta si ferma su una sessione già ferma, a cui claude stop risponde con un errore: {t['ferma']}"
    node = shutil.which("node")
    if not node:
        return None
    for nome in ("sessioni", "comandi"):
        shutil.copyfile(mod / f"{nome}.js", casa / f"{nome}.mjs")
    r = subprocess.run([node, "--input-type=module", "-e",
                        PROVA_SPOSTA_TUTTO % (json.dumps((casa / "sessioni.mjs").as_uri()), json.dumps((casa / "comandi.mjs").as_uri()))],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["suStudio"] != ["a1", "a2"] or g["suQui"] != ["a3"]:
        return f"spostabili() sbaglia chi va: {g['suStudio']} {g['suQui']}"
    if [x["testo"] for x in g["conto"]] != ["2 sessioni, 1 a turno finito", "1 sessione", "niente da spostare"]:
        return f"contoTutto() sbaglia il conto: {g['conto']}"
    if g["lavora"] is not None or not g["interattiva"]:
        return f"nonSiSposta() rifiuta chi lavora o accetta un'interattiva: {g['lavora']} {g['interattiva']}"
    if g["menu"] != [True, False]:
        return f"menu() non ha Sposta su… in background, o ce l'ha su un'interattiva: {g['menu']}"
    if g["per"] != {"id": "a1", "sessionId": "s1", "host": "qui", "macchina": "Torre", "tipo": "background", "stato": "ferma", "titolo": "Prova", "progetto": None}:
        return f"perSposta() passa al popup altro: {g['per']}"
    if g["tutto"] != [{"verbo": "volta-spostatutto", "arg": "torre-due", "lungo": False}, {"macchina": "torre-due", "id": "a1b2"}]:
        return f"instrada() non legge volta-spostatutto-<macchina>: {g['tutto']}"
    return None



def hz105(repo: Path, casa: Path) -> str | None:
    mod = repo / "shared/volta/mods/arturo"
    mj = (mod / "misure.js").read_text(encoding="utf-8")
    bj = (mod / "barra.js").read_text(encoding="utf-8")
    cj = (mod / "comuni.js").read_text(encoding="utf-8")
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for nome in ("SPAZIO", "MARGINE", "RAGGIO", "TESTO", "PULSANTE", "ICONA_MISURA", "PALLINO", "PIEDE"):
        if f"export const {nome} = " not in mj:
            return f"misure.js non esporta {nome}"
    if "export const MARGINE = SPAZIO.l;" not in mj:
        return "misure.js: il margine della colonna non viene dalla scala degli spazi"
    cima = bj[bj.find("const campo = "):bj.find("export class Piede {")]
    for pezzo, guasto in (
        ('h_flex().id("cerca")', "la cima non ha il campo Cerca o chiedi"),
        (".on_click(() => apriFinestra())", "il campo Cerca o chiedi non apre la ricerca"),
        ('.child("Cerca o chiedi"))', "il campo non dice Cerca o chiedi"),
        (".child(tasti().apri))", "il campo non scrive il tasto della ricerca"),
        ('pulsanteIcona("nuova", "square-pen", `Nuova richiesta · ${tasti().tessere}`, () => nuova(), { forte })', "Nuova richiesta non è l'icona accanto al campo"),
        ('.id("barra-cima").flex_none().px(MARGINE)', "la cima non parte dal margine comune"),
    ):
        if pezzo not in cima:
            return f"barra.js: {guasto}"
    if 'pulsante("apri", "folder", "Apri un progetto"' in bj:
        return "barra.js: Apri un progetto è ancora un pulsante della colonna"
    piede = bj[bj.find("export class Piede {"):]
    if piede.count("pulsanteIcona(") != 5 or "voce(" in piede:
        return "barra.js: il piede non è una fila di cinque pulsanteIcona"
    if "segnale: segnaleImpostazioni(Boolean(updates().app.ready))" not in piede:
        return "barra.js: l'icona di Impostazioni non ha il pallino dell'avviso o dell'app pronta"
    pi = cj[cj.find("export function pulsanteIcona("):cj.find("// La finestra")]
    for pezzo in (".tooltip(testo)", ".accessibility_label(testo)", 'PULSANTE[misura === "piccolo" ? "piccolo" : "grande"]'):
        if pezzo not in pi:
            return f"comuni.js: pulsanteIcona senza {pezzo}"
    if 'if (rigaMod(shared("arturo.mod"))?.avviso) return "blocked";' not in cj:
        return "comuni.js: segnaleImpostazioni non accende il rosso per un avviso del mod"
    if "h(PULSANTE[grande ? \"grande\" : \"piccolo\"])" not in cj:
        return "comuni.js: pulsante() non prende la misura"
    for pezzo, guasto in (
        ('.id(`vr-${s.host}-${s.id}`).relative().mx(MARGINE)', "le righe non partono dal margine comune"),
        ('.id(`vgh-${g.chiave || "senza"}`).mx(MARGINE)', "le testate dei gruppi non partono dal margine comune"),
        ('return h_flex().mx(MARGINE).mb(SPAZIO.s).h(PULSANTE.piccolo)', "l'interruttore non parte dal margine comune"),
        (".font_family(fontTerminale())", "lo schermo di claude logs ha ancora il font scritto fisso"),
        ("const f = settings()?.font;", "fontTerminale non legge le impostazioni"),
        ("un progetto si apre da Cerca (${tasti().apri}) o dalle tessere (${tasti().tessere})", "il vuoto dell'elenco cita ancora Apri un progetto"),
    ):
        if pezzo not in vj:
            return f"volta.js: {guasto}"
    if 'font_family("Atkinson Hyperlegible Mono").text_size(11.5)' in vj:
        return "volta.js: lo schermo di claude logs ha ancora il font scritto fisso"
    return None



# HZ106: il claude finto della SONDA, multipiattaforma. Elenca le sessioni di HZ_AGENTI.
CLAUDE_FINTO_NASCITE = r"""import json, os, sys
if sys.argv[1:2] == ["agents"]:
    print(os.environ.get("HZ_AGENTI", "[]"))
"""


def claude_finto_ovunque(bindir: Path, codice: str) -> None:
    """Un claude finto che shutil.which trova anche su Windows: claude.cmd che lancia lo script Python."""
    bindir.mkdir(parents=True, exist_ok=True)
    py = bindir / "claude_finto.py"
    py.write_text(codice, encoding="utf-8")
    if os.name == "nt":
        (bindir / "claude.cmd").write_text(f'@"{sys.executable}" "{py}" %*\r\n', encoding="utf-8")
    else:
        cl = bindir / "claude"
        cl.write_text(f"#!/bin/sh\nexec \"{sys.executable}\" \"{py}\" \"$@\"\n", encoding="utf-8")
        os.chmod(cl, 0o755)


def lavoro_finto(jobs: Path, nome: str, stato: str, creato: str, aggiornato: str, detail: str = "", intent: str = "", eta: float = 0) -> None:
    (jobs / nome).mkdir(parents=True, exist_ok=True)
    f = jobs / nome / "state.json"
    f.write_text(json.dumps({"state": stato, "detail": detail, "intent": intent, "createdAt": creato, "updatedAt": aggiornato}), encoding="utf-8")
    if eta:
        t = time.time() - eta
        os.utime(f, (t, t))


def hz106(repo: Path, casa: Path) -> str | None:
    """Le nascite che cadono e il congedo nella SONDA, e la voce della macchina nel documento."""
    mod = repo / "shared/volta/mods/arturo"
    bindir = casa / "bin"
    claude_finto_ovunque(bindir, CLAUDE_FINTO_NASCITE)
    hcf = casa / "hc_finto.py"
    hcf.write_text('print(\'{"machines": []}\')\n', encoding="utf-8")
    conf = casa / "conf"
    jobs = conf / "jobs"
    jobs.mkdir(parents=True)
    agenti = [{"id": "cg01", "sessionId": "cg01-x", "kind": "background", "state": "working", "status": "idle", "pid": 1, "cwd": "/p"},
              {"id": "nc01", "sessionId": "nc01-x", "kind": "background", "state": "working", "status": "idle", "pid": 2, "cwd": "/p"}]
    lavoro_finto(jobs, "cg01", "working", "2026-11-13T08:00:00.000Z", "2026-11-13T08:00:00.000Z", intent="/fine congedo da Volta: la persona ha chiuso questa sessione.", eta=7200)
    lavoro_finto(jobs, "nc01", "working", "2026-11-13T08:00:00.000Z", "2026-11-13T08:00:00.000Z", intent="/inizio volta", eta=7200)
    rotto = "exit 1 before init — …/$bunfs/root/chunk-3zne3bbr.js:11:20730) Bun v1.4.4 (macOS arm64)"
    for i, n in enumerate(("ko01", "ko02", "ko03")):
        lavoro_finto(jobs, n, "failed", "2026-11-13T12:00:00.000Z", f"2026-11-13T12:3{i}:00.000Z", detail=rotto)
    env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}", "VOLTA_HC": json.dumps([sys.executable, str(hcf)]),
           "CLAUDE_CONFIG_DIR": str(conf), "PYTHONIOENCODING": "utf-8", "HZ_AGENTI": json.dumps(agenti)}
    env.pop("VOLTA_SONDA_LOCALE", None)

    def leggi() -> dict | str:
        r = subprocess.run([sys.executable, str(mod / "volta_sonda.py"), "volta"], capture_output=True, text=True, encoding="utf-8", timeout=90, env=env)
        try:
            return json.loads(r.stdout)
        except ValueError:
            return f"volta_sonda.py volta senza JSON: {(r.stdout + r.stderr).strip()[-200:]}"

    d = leggi()
    if isinstance(d, str):
        return d
    qui = next((m for m in d.get("macchine", []) if m.get("questa")), {})
    n = qui.get("nascita") or {}
    if n.get("rotta") is not True or n.get("quante") != 3 or n.get("motivo") != "exit 1 before init" or n.get("da") != "2026-11-13T12:30:00.000Z":
        return f"tre crash before init su tre lavori: la macchina non risulta rotta ({qui})"
    righe = {x["sessionId"]: x.get("congedo") for x in d.get("sessioni", [])}
    if righe != {"cg01-x": True, "nc01-x": False}:
        return f"il congedo non viene dall'intento del lavoro: {righe}"
    # un lavoro nato dopo l'ultimo crash e in piedi: le sessioni partono di nuovo
    lavoro_finto(jobs, "ok01", "done", "2026-11-13T12:40:00.000Z", "2026-11-13T12:41:00.000Z")
    d = leggi()
    if isinstance(d, str):
        return d
    if any(m.get("nascita") for m in d.get("macchine", [])):
        return "una sessione nata e finita dopo i crash non toglie l'avviso"
    shutil.rmtree(jobs / "ok01")
    # crash vecchi di 40 minuti: fuori dalla finestra
    for nome in ("ko01", "ko02", "ko03"):
        t = time.time() - 2400
        os.utime(jobs / nome / "state.json", (t, t))
    d = leggi()
    if isinstance(d, str):
        return d
    if any(m.get("nascita") for m in d.get("macchine", [])):
        return "crash di 40 minuti fa tengono la macchina rotta"
    return None


PROVA_NASCITE = r"""
const S = await import(%s);
const dati = { macchine: [{ macchina: "Torre", host: "qui", questa: true },
  { macchina: "studio", host: "studio", questa: false, nascita: { rotta: true, da: "2026-11-13T12:30:13Z", quante: 9 } },
  { macchina: "spenta", host: "spenta", questa: false, irraggiungibile: "giù", nascita: { rotta: true, da: "2026-11-13T12:30:13Z", quante: 9 } }],
  sessioni: [{ macchina: "studio", host: "studio", sessionId: "s1", id: "a1", stato: "errore", ultimo: "2026-11-13T12:00:00Z" }] };
const prima = S.nascitePerAvviso(dati, {}), dopo = S.nascitePerAvviso(dati, prima.viste);
const guarito = S.nascitePerAvviso({ macchine: [{ host: "studio", macchina: "studio" }] }, prima.viste);
console.log(JSON.stringify({
  rotta: S.riparteAlClic({ stato: "errore", host: "studio" }, dati),
  buona: S.riparteAlClic({ stato: "errore", host: "qui" }, dati),
  viva: S.riparteAlClic({ stato: "ferma", host: "studio" }, dati),
  prima, dopo: dopo.avvisi, guarito: guarito.viste,
  senzaOra: S.avvisoNascita({ macchina: "studio", da: "", quante: 0 }),
  macchina: S.gruppi(dati).map((g) => [g.titolo, g.nota ?? null]),
  progetto: S.gruppi(dati, "progetto").map((g) => g.nota ?? null),
}));
"""


def hz107(repo: Path, casa: Path) -> str | None:
    """Niente ripartenza al clic su una macchina che non fa partire sessioni, avviso una volta, Arturo con un tempo massimo."""
    mod = repo / "shared/volta/mods/arturo"
    dj = (mod / "dati.js").read_text(encoding="utf-8")
    a = dj.find("export async function apriSessione(")
    guardia = dj.find("if (rc.errore) return { errore: rc.errore };", a)
    prepara = dj.find('const a = await prepara(s, s.stato === "errore");', a)
    if a < 0 or guardia < 0 or prepara < 0 or guardia > prepara:
        return "apriSessione fa ripartire una sessione in errore prima di guardare la sua macchina"
    v = dj.find("async function veglia(")
    g_v, p_v = dj.find("if (rotta.errore) return { errore: rotta.errore };", v), dj.find("const a = await prepara(s, true);", v)
    if v < 0 or g_v < 0 or p_v < 0 or g_v > p_v:
        return "la veglia fa ripartire la sessione anche su una macchina che non fa partire sessioni"
    if "{ cwd: c.base, timeout: ARTURO_MAX_MS }" not in dj or "errore: ARTURO_APPESO" not in dj:
        return "arturo() non ha un tempo massimo, o non dice che è rimasto appeso"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    if "this.avvisaNascite();" not in vj or 'setShared("arturo.volta.nascite", viste)' not in vj:
        return "volta.js non avvisa delle nascite, o non ricorda gli avvisi dati"
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(mod / "sessioni.js", casa / "sessioni.mjs")
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_NASCITE % json.dumps((casa / "sessioni.mjs").as_uri())],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:200]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    e = g["rotta"].get("errore") or ""
    if g["rotta"].get("riparte") is not False or "Su studio le sessioni non partono dalle " not in e or "(9 volte)" not in e or "riavvia studio" not in e:
        return f"riparteAlClic fa ripartire su una macchina rotta, o non dice perché: {g['rotta']}"
    if g["buona"] != {"riparte": True} or g["viva"] != {"riparte": False}:
        return f"riparteAlClic sbaglia su una macchina buona o una sessione viva: {g['buona']} {g['viva']}"
    if len(g["prima"]["avvisi"]) != 1 or g["prima"]["viste"] != {"studio": True} or g["dopo"] != [] or g["guarito"] != {}:
        return f"l'avviso non arriva una volta sola per episodio: {g['prima']} {g['dopo']} {g['guarito']}"
    if g["senzaOra"] != "Su studio le sessioni non partono: Claude esce prima di iniziare (più volte). Spesso macOS aspetta un permesso sullo schermo di studio: rispondi lì, o riavvia studio.":
        return f"avvisoNascita senza ora né conto: {g['senzaOra']}"
    if ["studio", "Non fa partire sessioni nuove"] not in g["macchina"] or ["spenta", "Non risponde"] not in g["macchina"]:
        return f"il gruppo della macchina non dice che non fa partire sessioni: {g['macchina']}"
    if g["progetto"][-1] != "spenta non risponde · studio non fa partire sessioni":
        return f"la vista per progetto non nomina la macchina rotta: {g['progetto']}"
    return None


PROVA_ORFANI = r"""
const S = await import(%s);
const ora = Date.parse("2026-11-13T13:00:00Z");
const b = (x) => ({ questa: true, tipo: "background", congedo: true, sessionId: x.id + "-s", stato: "ferma", ultimo: "2026-11-13T12:40:00Z", ...x });
const dati = { sessioni: [b({ id: "viva", fineFatta: true }), b({ id: "riaperta", fineFatta: false }), b({ id: "errore", stato: "errore" }),
  b({ id: "salvata", chiusa: true, fineFatta: true }), b({ id: "fresca", ultimo: "2026-11-13T12:55:00Z", fineFatta: true }),
  b({ id: "lavora", stato: "lavora", fineFatta: true }), b({ id: "altrove", questa: false, fineFatta: true }),
  b({ id: "normale", congedo: false, fineFatta: true }), b({ id: "interattiva", tipo: "interattiva", fineFatta: true }),
  b({ id: "ritirata", dorme: true, fineFatta: false }), b({ id: "fermata", chiusa: true, fineFatta: false })] };
console.log(JSON.stringify({
  tutti: S.congediOrfani(dati, {}, ora).map((p) => [p.s.id, p.fai, Boolean(p.avviso)]),
  filtrati: S.congediOrfani(dati, { "qui:errore": { sessionId: "errore-s", id: "errore", host: "qui" } }, ora, new Set(["qui:viva", "qui:salvata"])).map((p) => p.s.id),
}));
"""


def hz108(repo: Path, casa: Path) -> str | None:
    """I congedi rimasti a metà: stop se vivi con /fine in fondo, rm se fermi, niente su chi è stato riaperto."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, perche in (("this.chiudiOrfani(cx); });", "nessun giro chiude i congedi rimasti a metà"),
                          ("congediOrfani(this.dati, this.congedi(), Date.now(), conScheda).find((x) => !this.orfaniNo.has(chiave(x.s)))", "il giro non salta le sessioni già rifiutate"),
                          ("this.orfaniNo.add(chiave(p.s));", "un rm rifiutato si riprova e si ridice a ogni giro"),
                          ("await azioneSessione(p.s, p.fai)", "il giro non usa l'azione della sonda")):
        if pezzo not in vj:
            return f"volta.js: {perche}"
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(mod / "sessioni.js", casa / "sessioni.mjs")
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_ORFANI % json.dumps((casa / "sessioni.mjs").as_uri())],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:200]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["tutti"] != [["viva", "stop", False], ["errore", "rm", True], ["salvata", "rm", False]]:
        return f"congediOrfani sceglie male: {g['tutti']}"
    if g["filtrati"] != ["salvata"]:
        return f"congediOrfani tocca un congedo nel registro o una viva con la scheda aperta, o salta una ferma con la scheda: {g['filtrati']}"
    return None



PROVA_VOLO = r"""
const S = await import(%s);
const T = 45000, ora = 1000000;
console.log(JSON.stringify({
  niente: S.voloArturo(undefined, ora, T), gira: S.voloArturo({ da: ora - 1000, p: 1 }, ora, T),
  oltre: S.voloArturo({ da: ora - 50000, p: 1 }, ora, T), appeso: S.voloArturo({ da: 0, appeso: ora - 60000 }, ora, T),
  riprova: S.voloArturo({ da: 0, appeso: ora - S.ARTURO_PAUSA_MS - 1 }, ora, T),
  win: S.tocca([String.raw`C:\Users\f\.cache\volta\sessioni.json`], "C:/Users/f/.cache/volta", "C:/Users/f/.cache/volta/sessioni.json"),
  mic: S.tocca(["/h/.cache/volta/microfono-rinnovo", "/h/.cache/volta/mod-git/arturo/volta.js"], "/h/.cache/volta", "/h/.cache/volta/sessioni.json"),
  radice: S.tocca(["/h/.cache/volta/"], "/h/.cache/volta", "/h/.cache/volta/sessioni.json"),
  vuoto: S.tocca([], "/h/.cache/volta", "/h/.cache/volta/sessioni.json"),
}));
"""


def hz110(repo: Path, casa: Path) -> str | None:
    """Volta rilegge l'elenco solo per sessioni.json, e non accumula comandi di Arturo appesi."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    if "if (tocca(await watchFolder(this.cartella), this.cartella, this.file)) { await this.leggiSenzaFermarsi(cx); cx.notify(); }" not in vj:
        return "volta.js rilegge l'elenco a ogni file della cartella di Volta (clone del mod, microfono)"
    if 'setShared("arturo.volta.errore"' in vj:
        return "volta.js scrive ancora arturo.volta.errore a ogni giro, e nessuno lo legge"
    dj = (mod / "dati.js").read_text(encoding="utf-8")
    for pezzo, perche in (('if (passo.fai === "appeso") return { ok: false, errore: ARTURO_APPESO };', "un comando appeso non ferma i lanci nuovi"),
                          ('if (passo.fai === "aspetta") return voli[chiave].p;', "due chiamate uguali lanciano due processi"),
                          ("if (r.errore === ARTURO_APPESO) voli[chiave] = { da: voli[chiave].da, appeso: Date.now() };", "un comando appeso non si ricorda"),
                          ("c.base], { timeout: 15000 });", "cartelle() aspetta i 30 s di serie")):
        if pezzo not in dj:
            return f"dati.js: {perche}"
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(mod / "sessioni.js", casa / "sessioni.mjs")
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_VOLO % json.dumps((casa / "sessioni.mjs").as_uri())],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:200]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    passi = [g[k]["fai"] for k in ("niente", "gira", "oltre", "appeso", "riprova")]
    if passi != ["lancia", "aspetta", "appeso", "appeso", "lancia"]:
        return f"voloArturo sbaglia: {passi}, atteso lancia aspetta appeso appeso lancia"
    if [g["win"], g["mic"], g["radice"], g["vuoto"]] != [True, False, True, False]:
        return f"tocca sbaglia: windows {g['win']}, microfono {g['mic']}, cartella {g['radice']}, vuoto {g['vuoto']}"
    return None



PROVA_ESITO_SPOSTA = r"""
const S = await import(%s);
const dal = 1000000;
console.log(JSON.stringify({
  finito: S.esitoSposta(JSON.stringify({ finito: true, id: "n1", attach: ["claude", "attach", "n1"] }), dal, dal + 700000, "studio"),
  gira: S.esitoSposta(JSON.stringify({ finito: false, da: 1 }), dal, dal + 700000, "studio"),
  rotto: S.esitoSposta("{mezzo", dal, dal + 1000, "studio"),
  manca: S.esitoSposta(null, dal, dal + 1000, "studio"),
  tardi: S.esitoSposta(null, dal, dal + S.SPOSTA_MAX_MS + 1, "studio"),
  tetto: S.SPOSTA_MAX_MS,
}));
"""


def hz111(repo: Path, casa: Path) -> str | None:
    """Lo spostamento parte staccato e scrive l'esito in un file: Volta non dipende più dai 10 minuti di exec."""
    mod = repo / "shared/volta/mods/arturo"
    dj = (mod / "dati.js").read_text(encoding="utf-8")
    for pezzo, perche in (('"--titolo", titolo(s).slice(0, 60), "--esito", file], { timeout: 60000 }));', "lo spostamento non parte staccato, o aspetta più di un minuto la partenza"),
                          ("const p = esitoSposta(await readTextFile(file).catch(() => null), dal, Date.now(), nomeMacchina(macchina));", "Volta non legge l'esito dal file"),
                          ("await (dormi ? dormi(SPOSTA_OGNI_MS) : pausa(SPOSTA_OGNI_MS));", "le letture dell'esito non aspettano fra loro")):
        if pezzo not in dj:
            return f"dati.js: {perche}"
    if "1200000" in dj:
        return "dati.js chiede ancora a exec 20 minuti, oltre il tetto di 10 di Herdr"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    if "r = await spostaSessione(s, v.macchina, (ms) => cx.sleep(ms));" not in vj:
        return "volta.js non dà a spostaSessione l'attesa di cx.sleep"
    # il lato Python: risponde subito, il figlio staccato scrive l'esito, anche quando cade
    esito = casa / "sposta" / "s1.json"
    argv = [sys.executable, str(mod / "volta_sonda.py"), "sposta", "qui", "studio", "a1", "s1", "--cartella", str(casa), "--esito", str(esito)]
    env = {**os.environ, "VOLTA_SPOSTA_FINTO": json.dumps({"dorme": 3, "esito": {"id": "n1", "sessionId": "s1", "attach": ["claude", "attach", "n1"]}})}
    env.pop("VOLTA_SPOSTA_FIGLIO", None)
    t0 = time.time()
    r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=30, env=env)
    subito = time.time() - t0
    try:
        a = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return f"sposta --esito non risponde in JSON: {(r.stdout + r.stderr).strip()[-200:]}"
    if a != {"avviato": True, "esito": str(esito)} or subito > 2.5:
        return f"sposta --esito non risponde subito con avviato: {a} in {subito:.1f} s"
    try:
        prima = json.loads(esito.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "il file d'esito non c'è appena partito lo spostamento"
    if prima.get("finito") is not False:
        return f"il file d'esito dice finito prima della fine: {prima}"
    fine = None
    for _ in range(60):
        time.sleep(0.25)
        try:
            d = json.loads(esito.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if d.get("finito"):
            fine = d
            break
    if fine != {"id": "n1", "sessionId": "s1", "attach": ["claude", "attach", "n1"], "finito": True}:
        return f"il figlio staccato non scrive l'esito finito: {fine}"
    rotto = casa / "sposta" / "s2.json"
    env2 = {**env, "VOLTA_SPOSTA_FINTO": json.dumps({"rompi": True})}
    subprocess.run(argv[:-1] + [str(rotto)], capture_output=True, text=True, timeout=30, env=env2)
    caduto = None
    for _ in range(40):
        time.sleep(0.25)
        try:
            d = json.loads(rotto.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if d.get("finito"):
            caduto = d
            break
    if not caduto or "lo spostamento è caduto" not in (caduto.get("errore") or ""):
        return f"uno spostamento che cade non scrive finito con l'errore: {caduto}"
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(mod / "sessioni.js", casa / "sessioni.mjs")
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_ESITO_SPOSTA % json.dumps((casa / "sessioni.mjs").as_uri())],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:200]}"
    g = json.loads(r.stdout.strip().splitlines()[-1])
    if g["finito"] != {"fatto": {"id": "n1", "attach": ["claude", "attach", "n1"]}}:
        return f"esitoSposta non dà l'esito finito senza il campo finito: {g['finito']}"
    if g["gira"] != {"attendi": True} or g["rotto"] != {"attendi": True} or g["manca"] != {"attendi": True}:
        return f"esitoSposta non aspetta un file che gira, mezzo scritto o assente: {g['gira']} {g['rotto']} {g['manca']}"
    if g["tetto"] <= 600000 or "studio non ha finito in 25 minuti" not in (g["tardi"].get("errore") or ""):
        return f"esitoSposta non arriva oltre i 10 minuti di exec, o non lo dice: {g['tetto']} {g['tardi']}"
    return None


PROVA_PROGETTO = r"""
import { progettoDi, chiaveProgetto, titoloNoto, impostaProgetti } from "./sessioni.mjs";
import { canonico, spazio, aggancia, apri, slug } from "./dati.mjs";
import { lanciati } from "./herdr.mjs";
const noti = JSON.parse(process.env.HZ_SHARED)["arturo.progetti"];
const fonte = [progettoDi("volta", noti), progettoDi("Volta Celeste", noti), progettoDi("Due Mondi", noti), progettoDi("", noti), progettoDi(null, noti)];
const senza = progettoDi("volta", {});
impostaProgetti(noti);
const chiavi = ["volta", "volta-celeste", "herdr-arturo", "due-mondi", ""].map(chiaveProgetto);
const titoli = ["volta", "due-mondi"].map(titoloNoto);
const canonici = ["volta", "Volta Celeste", "Due Mondi"].map(canonico);
const spazi = ["volta", "herdr-arturo", "due-mondi", "niente"].map((n) => spazio(n)?.id ?? null);
aggancia({ progetto: process.env.HZ_PROGETTO, id: "aaaa1111", sessionId: "aaaa1111-s", nome: "prova", host: "qui" }, ["claude", "attach", "aaaa1111"]);
const agganciata = lanciati.splice(0);
await apri("volta");
console.log(JSON.stringify({ fonte, senza, chiavi, titoli, canonici, spazi, agganciata, aperta: lanciati.splice(0), stessoSlug: slug("Due Mondì") }));
"""


def hz113(repo: Path, casa: Path) -> str | None:
    mod_dir = repo / "shared/volta/mods/arturo"
    testata = (mod_dir / "testata.js").read_text(encoding="utf-8")
    if 'progettoDi(s.name, shared("arturo.progetti")).titolo ?? s.name' not in testata:
        return "testata.js non legge il titolo del progetto aperto con progettoDi"
    if "const aperto = progettoDi(spaces().find((x) => x.active)?.name).chiave;" not in (mod_dir / "volta.js").read_text(encoding="utf-8"):
        return "volta.js non legge il progetto dello spazio aperto con progettoDi"
    dati = (mod_dir / "dati.js").read_text(encoding="utf-8")
    if "export const slug" in dati or "export { slug };" not in dati:
        return "dati.js ha ancora una sua copia di slug: la copia sola sta in sessioni.js"
    node = shutil.which("node")
    if not node:
        return None
    mod = casa / "mod"
    mod.mkdir()
    mod_dati(repo, mod, dati)
    (mod / "prova.mjs").write_text(PROVA_PROGETTO, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python3", str(casa / "bin" / "arturo")], "radice": str(repo), "base": str(casa)}), encoding="utf-8")
    voce = {"chiave": "herdr-arturo", "titolo": "Volta"}
    noti = {"herdr-arturo": voce, "volta": voce, "volta-celeste": voce, "due-mondi": {"chiave": "due-mondi", "titolo": "Due mondi"}}
    condivisi = json.dumps({"arturo.progetti": noti, "arturo.volta.macchine": [], "arturo.dove": "qui"})

    def gira(spazi, progetto="volta"):
        r = subprocess.run([node, str(mod / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=30,
                           env={**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa), "HZ_SHARED": condivisi,
                                "HZ_HERDR": json.dumps({"spaces": spazi}), "HZ_PROGETTO": progetto})
        if r.returncode != 0:
            raise RuntimeError(f"dati.js non gira: {(r.stderr or r.stdout).strip()[-200:]}")
        return json.loads(r.stdout.strip().splitlines()[-1])

    def nuove(d):
        return [x for x in d["agganciata"] if x["cmd"] in ("tab.new", "space.new")]

    vecchio = {"id": "s1", "name": "Volta", "named": True}
    d = gira([vecchio, {"id": "s2", "name": "herdr-arturo", "named": True}, {"id": "s3", "name": "due-mondi", "named": True},
              {"id": "s9", "name": "herdr-arturo", "named": True, "machine": "torre"}])
    atteso = [{"chiave": "herdr-arturo", "titolo": "Volta"}, {"chiave": "herdr-arturo", "titolo": "Volta"},
              {"chiave": "due-mondi", "titolo": "Due mondi"}, {"chiave": "", "titolo": None}, {"chiave": "", "titolo": None}]
    if d["fonte"] != atteso:
        return f"progettoDi: {d['fonte']}"
    if d["senza"] != {"chiave": "volta", "titolo": None}:
        return f"progettoDi senza progetti noti dà lo slug: {d['senza']}"
    if d["chiavi"] != ["herdr-arturo", "herdr-arturo", "herdr-arturo", "due-mondi", ""] or d["titoli"] != ["Volta", "Due mondi"]:
        return f"chiaveProgetto e titoloNoto non passano da progettoDi: {d['chiavi']} {d['titoli']}"
    if d["canonici"] != ["herdr-arturo", "herdr-arturo", "due-mondi"]:
        return f"canonico: {d['canonici']}"
    if d["spazi"] != ["s2", "s2", "s3", None]:
        return f"spazio(): {d['spazi']}, atteso lo spazio herdr-arturo di questa macchina e mai il libero Volta"
    n = nuove(d)
    if len(n) != 1 or n[0]["cmd"] != "tab.new" or n[0].get("space") != "s2":
        return f"aggancia di una sessione di volta: {d['agganciata']}, attesa una scheda nello spazio herdr-arturo"
    if d["aperta"] != [{"cmd": "space.select", "id": "s2"}]:
        return f"apri(volta) (Lavoraci) non va nello spazio della sessione: {d['aperta']}"
    if d["stessoSlug"] != "due-mondi":
        return f"slug di dati.js non è quello di sessioni.js: {d['stessoSlug']}"
    # senza lo spazio del progetto: nasce uno spazio herdr-arturo, non uno "volta" che libera() rinominerebbe
    d = gira([vecchio])
    n = nuove(d)
    if len(n) != 1 or n[0]["cmd"] != "space.new" or n[0].get("name") != "herdr-arturo":
        return f"aggancia senza lo spazio del progetto: {d['agganciata']}, atteso uno spazio nuovo herdr-arturo"
    # lo spazio del progetto col nome alternativo (scritto dalla persona) è lo stesso progetto
    d = gira([vecchio, {"id": "s4", "name": "Volta Celeste", "named": True}], "herdr-arturo")
    n = nuove(d)
    if len(n) != 1 or n[0]["cmd"] != "tab.new" or n[0].get("space") != "s4":
        return f"aggancia con lo spazio Volta Celeste: {d['agganciata']}, attesa una scheda in s4"
    # una sessione senza progetto va ancora nello spazio libero di prima
    d = gira([vecchio, {"id": "s2", "name": "herdr-arturo", "named": True}], "")
    n = nuove(d)
    if len(n) != 1 or n[0].get("space") != "s1":
        return f"una sessione senza progetto non va nello spazio libero: {d['agganciata']}"
    return None


PROVA_MACCHINA = r"""
import { nomeMacchina as nomeSessioni, macchinaQui } from "./sessioni.mjs";
import { nomeMacchina, nuova } from "./dati.mjs";
import { avvisi } from "./herdr.mjs";
const elenco = [{ host: "qui", macchina: "Torre", questa: true }, { host: "Studio", macchina: "Studio", questa: false }];
const puri = [nomeSessioni("qui", elenco), nomeSessioni("qui", { macchine: elenco }), nomeSessioni("qui", []), nomeSessioni("Studio", elenco),
  macchinaQui({ macchine: elenco }), macchinaQui(null)];
await nuova("ciao");
console.log(JSON.stringify({ puri, dati: [nomeMacchina("qui"), nomeMacchina("Studio")], avvisi }));
"""

PROVA_CHI = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("volta_sonda", sys.argv[1])
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)
print(json.dumps({"qui": vs.chi("qui"), "vuoto": vs.chi(""), "niente": vs.chi(None), "torre": vs.chi("Torre"), "vero": vs.nome_qui()}))
"""


def hz114(repo: Path, casa: Path) -> str | None:
    mod_dir = repo / "shared/volta/mods/arturo"
    sonda = (mod_dir / "volta_sonda.py").read_text(encoding="utf-8")
    sposta = (mod_dir / "volta_sposta.py").read_text(encoding="utf-8")
    if 'or "questa macchina"' in sonda or sonda.count("chi(nome)") < 7:
        return 'volta_sonda.py: gli errori scrivono ancora nome or "questa macchina", che per "qui" dice "qui"'
    if "def chi(" in sposta or sposta.count("vs.chi(") < 9:
        return "volta_sposta.py ha una sua copia di chi(): la copia sola sta in volta_sonda.py"
    prova = casa / "prova_chi.py"
    prova.write_text(PROVA_CHI, encoding="utf-8")
    r = subprocess.run([sys.executable, str(prova), str(mod_dir / "volta_sonda.py")], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return f"volta_sonda.py non si carica: {(r.stderr or r.stdout).strip()[-200:]}"
    c = json.loads(r.stdout.strip().splitlines()[-1])
    if not c["vero"] or c["vero"] == "qui" or [c["qui"], c["vuoto"], c["niente"]] != [c["vero"]] * 3 or c["torre"] != "Torre":
        return f"chi(): {c}"
    node = shutil.which("node")
    if not node:
        return None
    mod = casa / "mod"
    mod.mkdir()
    mod_dati(repo, mod, (mod_dir / "dati.js").read_text(encoding="utf-8"))
    (mod / "prova.mjs").write_text(PROVA_MACCHINA, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python3", str(casa / "bin" / "arturo")], "radice": str(repo), "base": str(casa)}), encoding="utf-8")
    condivisi = {"arturo.volta.macchine": [{"host": "qui", "macchina": "Torre", "questa": True, "giu": False}], "arturo.dove": "qui"}
    r = subprocess.run([node, str(mod / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=30,
                       env={**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa), "HZ_SHARED": json.dumps(condivisi),
                            "HZ_EXEC": json.dumps({"errore": "il servizio di Claude non parte su Torre: spento"})})
    if r.returncode != 0:
        return f"dati.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["puri"] != ["Torre", "Torre", "questa macchina", "Studio", "Torre", None]:
        return f"nomeMacchina e macchinaQui di sessioni.js: {d['puri']}"
    if d["dati"] != ["Torre", "Studio"]:
        return f"nomeMacchina di dati.js non legge l'elenco delle macchine: {d['dati']}"
    titoli = [a.get("title") for a in d["avvisi"]]
    if titoli != ["La sessione non nasce su Torre"]:
        return f"l'avviso di una nascita fallita: {titoli}, atteso il nome della macchina"
    return None


def hz115(repo: Path, casa: Path) -> str | None:
    mod_dir = repo / "shared/volta/mods/arturo"
    copia = casa / "mod-py"
    copia.mkdir()
    for nome in ("volta_sonda.py", "volta_sposta.py", "volta_note.py", "volta_microfono.py"):
        shutil.copyfile(mod_dir / nome, copia / nome)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    for argv in (["volta_sonda.py", "sposta"], ["volta_note.py"]):
        subprocess.run([sys.executable, *argv], cwd=copia, capture_output=True, text=True, timeout=60, env=env)
        cache = copia / "__pycache__"
        if cache.exists():
            return f"{' '.join(argv)} lascia {sorted(x.name for x in cache.iterdir())} nella cartella del mod: Herdr lo ricarica"
    return None

PROVA_F2_PAUSA = r"""
import { pausa, impostaDormi } from "./dati.mjs";
import { eseguiti } from "./herdr.mjs";
const python = () => eseguiti.filter((x) => x.includes("-c")).length;
const out = {};
await pausa(5);
out.senza = python();
const chiesti = [];
impostaDormi(async (ms) => { chiesti.push(ms); });
await pausa(400);
out.orologio = { chiesti, python: python() };
let gettate = 0;
impostaDormi(async () => { gettate++; throw new Error("copia ricaricata"); });
await pausa(5);
await pausa(5);
out.getta = { python: python(), gettate };
console.log(JSON.stringify(out));
"""

PROVA_F2_STATI = r"""
const S = await import(%s);
const viva = { id: "a1", stato: "lavora", host: "studio" }, ferma = { id: "a1", stato: "ferma", host: "qui" };
console.log(JSON.stringify({
  prima: S.statiCorti({ sessioni: [viva, ferma] }), dopo: S.statiCorti({ sessioni: [ferma, viva] }),
  ferme: S.statiCorti({ sessioni: [ferma, { ...ferma, host: "studio" }] }),
}));
"""


def hz117(repo: Path, casa: Path) -> str | None:
    """Le sei correzioni piccole della fase F2 (#5575-#5579)."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, perche in (("const guasto = this.errore || this.erroreLettura;", "la colonna non guarda l'errore della lettura dell'elenco (#5575)"),
                          ('.child(guasto ? "Non riesco a leggere le sessioni delle macchine."', "senza elenco l'errore della lettura non si vede (#5575)"),
                          ("const vecchio = this.dati && guasto && this.dati.letto ?", "con un elenco vecchio l'errore della lettura non si vede (#5575)")):
        if pezzo not in vj:
            return f"volta.js: {perche}"
    if 'JSON.parse((r.stdout || "").trim().split("\\n").pop()' in vj or vj.count("const d = esito(r);") != 2:
        return "volta.js legge ancora l'ultima riga delle risposte dei Python invece di esito() (#5578)"
    if 'risposta = d.errore && !d.stato ? { stato: "errore", motivo: d.errore } : d;' not in vj:
        return "volta.js: un errore del ponte del microfono non diventa lo stato errore (#5578)"
    if "impostaDormi((/** @type {number} */ ms) => cx.sleep(ms));" not in (mod / "main.js").read_text(encoding="utf-8"):
        return "main.js non dà a dati.js l'orologio di cx.sleep (#5579)"
    # #5576: un gesto su questa macchina con un PATH senza claude lo trova in ~/.local/bin
    bindir = casa / "casa" / ".local" / "bin"
    claude_finto_ovunque(bindir, "import sys\nprint('fermata ' + ' '.join(sys.argv[1:]))\n")
    prova = ("import json, sys; sys.dont_write_bytecode = True; sys.path.insert(0, sys.argv[1]); import volta_sonda as v, volta_sposta as s\n"
             "fuori = [n for n in ('SONDA', 'NASCI', 'SERVIZIO', 'CLAUDE_FUORI_PATH') if '#CLAUDE#' in getattr(v, n) or 'def trova_claude' not in getattr(v, n)]\n"
             "fuori += [] if 'def trova_claude' in s.TROVA else ['TROVA']\n"
             "print(json.dumps({'gesto': v.azione('qui', 'stop', 'abcd1234'), 'fuori': fuori}))")
    # su Windows l'installatore mette claude.exe, e il claude finto è un .cmd: lì il gesto non si prova
    env = {**os.environ, "HOME": str(casa / "casa"), "PATH": "/usr/bin:/bin"}
    if os.name == "nt":
        prova = prova.replace("v.azione('qui', 'stop', 'abcd1234')", "{'ok': True, 'testo': 'fermata stop abcd1234'}")
    r = subprocess.run([sys.executable, "-I", "-c", prova, str(mod)], capture_output=True, text=True, encoding="utf-8", timeout=60, env=env)
    if r.returncode != 0:
        return f"volta_sonda.py non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["fuori"]:
        return f"gli script per le macchine non hanno la ricerca sola di claude (#5576): {d['fuori']}"
    if d["gesto"] != {"ok": True, "testo": "fermata stop abcd1234"}:
        return f"un gesto su questa macchina non trova claude in ~/.local/bin (#5576): {d['gesto']}"
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(mod / "sessioni.js", casa / "sessioni.mjs")
    r = subprocess.run([node, "--input-type=module", "-e", PROVA_F2_STATI % json.dumps((casa / "sessioni.mjs").as_uri())],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[:160]}"
    st = json.loads(r.stdout.strip().splitlines()[-1])
    # doppio: l'id sta su due macchine, e un'etichetta col solo id non dice quale copia (#5634)
    viva = {"a1": {"stato": "lavora", "host": "studio", "doppio": True}}
    if st["prima"] != viva or st["dopo"] != viva or st["ferme"] != {"a1": {"stato": "ferma", "host": "studio", "doppio": True}}:
        return f"statiCorti non tiene la copia viva di un id doppio (#5577): {st}"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_F2_PAUSA, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_SHARED": "{}", "HZ_HERDR": "{}", "HZ_EXEC": "{}"}
    r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=60, env=e)
    if r.returncode != 0:
        return f"dati.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    pa = json.loads(r.stdout.strip().splitlines()[-1])
    if pa["senza"] != 1:
        return f"senza orologio pausa() non aspetta con Python: {pa}"
    if pa["orologio"] != {"chiesti": [400], "python": 1}:
        return f"con l'orologio pausa() lancia ancora Python, o non lo usa (#5579): {pa}"
    if pa["getta"] != {"python": 3, "gettate": 1}:
        return f"un orologio che getta non lascia il posto a Python, o viene richiamato (#5579): {pa}"
    return None


PROVA_STACCO = r"""
import { daStaccare, STACCA_DOPO_MS } from "./sessioni.mjs";
import { staccaAggancio, impostaDormi } from "./dati.mjs";
import { inviati } from "./herdr.mjs";
impostaDormi(async () => {});
const ora = Date.now(), fa = (min) => new Date(ora - min * 60000).toISOString();
const bg = (id, host, min, extra = {}) => ({ id, sessionId: `s-${id}-${host}`, host, tipo: "background", stato: "ferma", chi: "claude", interazione: fa(min), attach: ["claude", "attach", id], ...extra });
const sessioni = [bg("a1", "qui", 50), bg("a2", "qui", 30), bg("a3", "qui", 90, { stato: "lavora" }), bg("a4", "qui", 90, { stato: "aspetta" }),
  bg("a5", "qui", 90), bg("a6", "qui", 90), bg("a7", "qui", 90, { coda: "Lo lancio in background: ti aggiorno appena finisce." }),
  bg("b1", "qui", 90), bg("b1", "studio", 90, { stato: "lavora" }), bg("a9", "qui", 70), bg("a10", "qui", 90), bg("a11", "qui", 90, { chiusa: true })];
const scheda = (id, host) => ({ id, sessionId: `s-${id}-${host}`, host });
const schede = { t1: scheda("a1", "qui"), t2: scheda("a2", "qui"), t3: scheda("a3", "qui"), t4: scheda("a4", "qui"), t5: scheda("a5", "qui"),
  t6: scheda("a6", "qui"), t7: scheda("a7", "qui"), t8: scheda("b1", "studio"), t9: scheda("a9", "qui"), t10: scheda("a10", "qui"), t11: scheda("a11", "qui") };
const visti = new Set(Object.keys(schede).filter((k) => k !== "t6"));
const scelte = daStaccare(schede, sessioni, ora, { davanti: "t5", visti, no: new Set(["t10"]) }).map((x) => x.indirizzo);
const s = bg("a1", "qui", 50), sr = bg("b1", "studio", 90, { attach: ["ssh", "-t", "studio", "/x/claude", "attach", "b1"] });
const esiti = {};
for (const [t, x] of [["fg", s], ["altro", s], ["gia", s], ["resta", s], ["ssh", sr]]) {
  const prima = inviati.length;
  esiti[t] = { r: await staccaAggancio(t, x), tasti: inviati.slice(prima).filter((a) => a[0] === "keys") };
}
console.log(JSON.stringify({ scelte, dopo: STACCA_DOPO_MS, esiti }));
process.exit(0);
"""


def hz118(repo: Path, casa: Path) -> str | None:
    """Lo stacco delle schede ferme da 45 minuti e il riaggancio al clic (F3.2 di #5587)."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, perche in (("    cx.timer.every(OGNI_AUTO, (cx) => this.staccaFerme(cx));\n", "Volta non stacca le schede ferme a ogni giro"),
                          (" cx.notify(); this.riaggancia(k, cx); }", "la scheda staccata che torna in primo piano non si riaggancia"),
                          ("    this.apri(s, s.attach, false, cx);\n  }\n\n  // Il ponte del microfono", "il riaggancio non passa dalla strada del clic (apri)"),
                          ('davanti: focused()?.terminal ?? null, visti, no', "lo stacco non salta la scheda in primo piano o quelle fuori dai pannelli")):
        if pezzo not in vj:
            return f"volta.js: {perche}"
    node = shutil.which("node")
    if not node:
        return None
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_STACCO, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    vivo = lambda fg: {"state": "live", "pid": 10, "argv": ["claude", "attach", "a1"], "foreground": fg}  # noqa: E731
    shell = {"pid": 10, "argv": ["zsh"]}
    aggancio = {"pid": 11, "argv": ["claude", "attach", "a1"]}
    letture = {"fg": [vivo(aggancio), vivo(shell)], "altro": [vivo({"pid": 11, "argv": ["vim", "note.md"]})], "gia": [vivo(shell)],
               "resta": [vivo(aggancio), vivo(aggancio)],
               "ssh": [vivo({"pid": 12, "argv": ["ssh", "-t", "-o", "ConnectTimeout=10", "studio", "/x/claude", "attach", "b1"]}), vivo(shell)]}
    e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_SHARED": "{}", "HZ_HERDR": "{}", "HZ_EXEC": "{}",
         "HZ_HC_GET": json.dumps(letture)}
    r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=60, env=e)
    if r.returncode != 0:
        return f"dati.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["dopo"] != 45 * 60000:
        return f"la soglia dello stacco non è 45 minuti: {d['dopo']}"
    if d["scelte"] != ["t9", "t1"]:
        return f"daStaccare sceglie male (attese t9 poi t1, ferme da 70 e 50 minuti): {d['scelte']}"
    es = d["esiti"]
    ctrlz = [["keys", "fg", "ctrl+z"]]
    if es["fg"] != {"r": {"ok": True}, "tasti": ctrlz}:
        return f"lo stacco di un aggancio in primo piano non manda Ctrl+Z o non dice ok: {es['fg']}"
    if es["altro"]["tasti"] or "errore" not in es["altro"]["r"]:
        return f"lo stacco manda Ctrl+Z a un programma che non è l'aggancio: {es['altro']}"
    if es["gia"] != {"r": {"gia": True}, "tasti": []}:
        return f"una scheda che ha già la shell riceve Ctrl+Z: {es['gia']}"
    if "errore" not in es["resta"]["r"]:
        return f"lo stacco dice ok anche se claude attach resta in primo piano: {es['resta']}"
    if es["ssh"] != {"r": {"ok": True}, "tasti": [["keys", "ssh", "ctrl+z"]]}:
        return f"lo stacco non riconosce l'aggancio dentro ssh: {es['ssh']}"
    return None


PROVA_VOLO_SPOSTA = r"""
import { spostaSessione, riprendiSposta, spostamentiInVolo } from "./dati.mjs";
import { voloSposta, VOLO_FRESCO_MS, VOLO_MAX_MS } from "./sessioni.mjs";
import { lanciati } from "./herdr.mjs";
import { readFileSync, writeFileSync } from "node:fs";
const caso = process.env.HZ_CASO, dir = process.env.HZ_SPOSTA, ora = Date.now();
const s = { id: "a1", sessionId: "s1", host: "qui", questa: true, tipo: "background", nome: "Prova", attach: ["claude", "attach", "a1"] };
const file = `${dir}/s1.json`;
const leggi = (f) => { try { return JSON.parse(readFileSync(f, "utf-8")); } catch { return null; } };
let out = {};
if (caso === "puro") {
  const v = { s, macchina: "studio", file, dal: ora - 1000, chiuse: 1 };
  out = { mia: voloSposta({ ...v, preso: ora - VOLO_FRESCO_MS - 1 }, ora), senza: voloSposta(v, ora),
          altrui: voloSposta({ ...v, preso: ora - 1000 }, ora), vecchia: voloSposta({ ...v, dal: ora - VOLO_MAX_MS - 1 }, ora),
          rotta: voloSposta({ ...v, s: null }, ora), nulla: voloSposta(null, ora) };
} else if (caso === "volo") {
  // la ricarica: l'attesa di cx.sleep non torna più (qui getta), lo spostamento resta in volo.json
  try { await spostaSessione(s, "studio", async () => { throw new Error("ricarica"); }); } catch { /* atteso */ }
  out = { volo: await spostamentiInVolo() };
} else {
  const v = { s, macchina: "studio", file, dal: ora - 60000, chiuse: 1, preso: ora - 60000 };
  writeFileSync(`${dir}/volo.json`, JSON.stringify({ s1: v }), "utf-8");
  writeFileSync(file, JSON.stringify(caso === "fatto"
    ? { id: "n1", sessionId: "s1", attach: ["ssh", "-t", "studio", "claude", "attach", "n1"], macchina: "studio", finito: true }
    : { errore: "lost the line", finito: true }), "utf-8");
  const r = await riprendiSposta(v, async () => {});
  out = { r, volo: leggi(`${dir}/volo.json`), traccia: leggi(`${dir}/s1.traccia.json`), lanciati };
}
console.log(JSON.stringify(out));
process.exit(0);
"""


def hz116(repo: Path, casa: Path) -> str | None:
    """Uno spostamento che una ricarica del mod lascia a metà si riprende al caricamento (#5559)."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, perche in (("      this.riprendiVolo(cx);\n", "Volta non riprende gli spostamenti in volo al caricamento"),
                          ("try { r = await riprendiSposta(v, (ms) => cx.sleep(ms)); }", "la ripresa non aspetta con cx.sleep"),
                          ('if (che === "altrui" || this.faccio[chiave(v.s)]) { altrui = true; continue; }', "la ripresa prende anche uno spostamento che un'altra copia segue")):
        if pezzo not in vj:
            return f"volta.js: {perche}"
    node = shutil.which("node")
    if not node:
        return None
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_VOLO_SPOSTA, encoding="utf-8")
    app = casa / "app"
    sposta = app / "cache" / "volta" / "sposta"
    sposta.mkdir(parents=True)
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")

    def volta(caso, **extra):
        for f in sposta.iterdir():
            f.unlink()
        e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_CASO": caso, "HZ_SPOSTA": str(sposta),
             "HZ_SHARED": json.dumps({"arturo.volta.macchine": [], "arturo.dove": "qui"}), "HZ_HERDR": "{}", "HZ_NASCE": "t9", **extra}
        for k in ("HZ_EXEC", "HZ_EXEC_CODICE", "HZ_HC_GET", "HZ_HC_READ", "HZ_CHIUDE"):
            if k not in extra:
                e.pop(k, None)
        r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=60, env=e)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:300])
        return json.loads(r.stdout.strip().splitlines()[-1])

    g = volta("puro")
    if [g["mia"], g["senza"], g["altrui"], g["vecchia"], g["rotta"], g["nulla"]] != ["mia", "mia", "altrui", "scarta", "scarta", "scarta"]:
        return f"voloSposta sbaglia: {g}"
    g = volta("volo", HZ_EXEC=json.dumps({"avviato": True}))
    voci = {x["k"]: x["v"] for x in g["volo"]}
    v = voci.get("s1") or {}
    if v.get("macchina") != "studio" or (v.get("s") or {}).get("id") != "a1" or not str(v.get("file", "")).endswith("s1.json") \
            or not isinstance(v.get("dal"), (int, float)) or not isinstance(v.get("preso"), (int, float)):
        return f"uno spostamento staccato non resta segnato in volo.json: {g['volo']}"
    g = volta("fatto")
    nuove = [x for x in g["lanciati"] if x["cmd"] in ("tab.new", "space.new")]
    if g["r"] != {"ok": True} or not any("n1" in (x.get("argv") or []) for x in nuove):
        return f"la ripresa di uno spostamento finito non apre la scheda d'arrivo: {g['r']}, {nuove}"
    if "s1" in (g["volo"] or {}):
        return f"lo spostamento ripreso e finito resta in volo.json: {g['volo']}"
    if "ripresa" not in [x.get("passo") for x in g["traccia"] or []]:
        return "la traccia non dice che lo spostamento è stato ripreso"
    g = volta("male")
    male = [x for x in g["traccia"] or [] if x.get("passo") == "male"]
    if "lost the line" not in (g["r"].get("errore") or "") or not male or not male[-1].get("riaperta"):
        return f"la ripresa di uno spostamento andato male non riapre la scheda chiusa: {g['r']}, {male}"
    if "s1" in (g["volo"] or {}):
        return f"lo spostamento ripreso e andato male resta in volo.json: {g['volo']}"
    return None


PROVA_CHIAVE = r"""
const S = await import(process.env.HZ_SESSIONI);
const M = await import(process.env.HZ_MICROFONO);
// dopo Sposta su: a1 c'è qui (ferma) e su amaltea (viva); il /clear di là ha cambiato il sessionId
const qui = { id: "a1", sessionId: "a1-x", host: "qui", questa: true, tipo: "background", stato: "ferma", attach: ["/u/claude", "attach", "a1"] };
const la = { id: "a1", sessionId: "c9-y", host: "amaltea", macchina: "amaltea", tipo: "background", stato: "lavora",
  attach: ["ssh", "-t", "amaltea", "/m/claude", "attach", "a1"] };
const l = [qui, la];
const t = (argv, et) => ({ address: "t1", argv, labels: et ? { "arturo.sessione": et } : {} });
const host = (x) => x?.host ?? null;
const studio = { ...la, host: "studio", macchina: "studio", attach: ["ssh", "-t", "studio", "/m/claude", "attach", "a1"] };
console.log(JSON.stringify({
  chiave: S.chiave(la),
  ssh: [S.sshDi(S.argvScheda(la.attach)), S.sshDi(["sh", "-c", "while :; do ssh -t -o X=1 io@Amaltea claude attach a1; done"]),
        S.sshDi(["pwsh", "-Command", "& 'C:\\W\\ssh.exe' '-t' 'amaltea' 'attach' 'a1'"]), S.sshDi(qui.attach)],
  scheda: [host(S.sessioneDi(t(S.argvScheda(la.attach)), l)), host(S.sessioneDi(t(qui.attach), l)),
           host(S.sessioneDi(t(["zsh"], "amaltea:a1"), l)), host(S.sessioneDi(t(["zsh"], "a1"), l)),
           host(S.sessioneDi(t(["zsh"], "a1"), [la])), host(S.sessioneDi(t(qui.attach, "amaltea:a1"), l))],
  vis: S.visibili({ sessioni: l }).sessioni.map(S.chiave),
  congedo: S.visibili({ sessioni: [{ ...qui, stato: "ferma" }, { ...la, stato: "ferma" }] }, { "amaltea:a1": { id: "a1", host: "amaltea" } }).sessioni.map(S.chiave),
  trova: host(S.trova(l, { id: "a1", host: "amaltea", sessionId: "a1-x" })),
  stati: S.statiCorti({ sessioni: l }),
  mic: [M.bersaglio(t(["zsh"], "studio:a1"), [la, studio])?.target ?? null, M.bersaglio(t(["zsh"], "amaltea:a1"), [la, studio])?.target ?? null],
}));
"""

PROVA_CHIAVE_DATI = r"""
import { schedeDi, schedeAgganciate } from "./dati.mjs";
import { setShared } from "./herdr.mjs";
const qui = { id: "a1", sessionId: "a1-x", host: "qui", questa: true, tipo: "background", stato: "ferma", attach: ["/u/claude", "attach", "a1"] };
const la = { id: "a1", sessionId: "c9-y", host: "amaltea", tipo: "background", stato: "lavora", attach: ["ssh", "-t", "amaltea", "/m/claude", "attach", "a1"] };
const ind = (l) => l.map((x) => x.address);
const out = { qui: ind(schedeDi(qui)), la: ind(schedeDi(la)),
  agganciate: Object.fromEntries(Object.entries(schedeAgganciate([qui, la])).map(([a, s]) => [a, s.host])) };
// l'id sta su due macchine: l'etichetta vecchia col solo id (t3) non dice più di chi è la scheda
setShared("arturo.volta.stati", { a1: { stato: "lavora", host: "amaltea", doppio: true } });
out.doppioQui = ind(schedeDi(qui));
out.doppioLa = ind(schedeDi(la));
console.log(JSON.stringify(out));
"""


def hz119(repo: Path, casa: Path) -> str | None:
    """La chiave macchina:id delle sessioni di Volta (S1 del piano F3·S, #5634)."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    for pezzo, perche in (("      const s = trova(this.dati?.sessioni, c) ?? undefined;", "il passo del congedo prende la riga per sessionId, anche la copia ferma"),
                          ("    const s = trova(this.dati?.sessioni, c);\n    if (!s || s.tipo !== \"background\" || chiusa(s) || this.congedi()[chiave(s)]) return;", "il congedo non va per macchina e id"),
                          ("    return Object.fromEntries(Object.entries(m).map(([k, c]) => [c?.id ? chiave(c) : k, c]));", "i congedi scritti prima del 14/11 non passano alla chiave"),
                          ("      const s = vive.find((x) => chiave(x) === k);", "la coda di Sposta riconosce la sessione dal solo sessionId")):
        if pezzo not in vj:
            return f"volta.js: {perche}"
    if "sessionId" in "".join(re.findall(r"this\.(?:apro|veglio|faccio|codaSposta|sposto|avvisi|congedo|escono|porto|inizio)\[[^\]]*\]", vj)):
        return "volta.js: una mappa delle sessioni va ancora per sessionId"
    node = shutil.which("node")
    if not node:
        return None
    shutil.copyfile(mod / "sessioni.js", casa / "sessioni.mjs")
    shutil.copyfile(mod / "microfono.js", casa / "microfono.mjs")
    (casa / "prova.mjs").write_text(PROVA_CHIAVE, encoding="utf-8")
    e = {**os.environ, "HZ_SESSIONI": (casa / "sessioni.mjs").as_uri(), "HZ_MICROFONO": (casa / "microfono.mjs").as_uri()}
    r = subprocess.run([node, str(casa / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=30, env=e)
    if r.returncode != 0:
        return f"sessioni.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["chiave"] != "amaltea:a1":
        return f"la chiave di una sessione non è macchina:id: {d['chiave']}"
    if d["ssh"] != ["amaltea", "amaltea", "amaltea", None]:
        return f"sshDi non legge la macchina dell'aggancio (argv, sh -c, PowerShell, locale): {d['ssh']}"
    # la scheda ssh è di amaltea, quella locale di qui; l'etichetta nuova decide, quella vecchia solo se l'id è unico
    if d["scheda"] != ["amaltea", "qui", "amaltea", None, "amaltea", "amaltea"]:
        return f"una scheda non riconosce la copia giusta di un id su due macchine: {d['scheda']}"
    if d["vis"] != ["amaltea:a1"]:
        return f"l'elenco mostra la copia ferma accanto a quella viva dopo un /clear: {d['vis']}"
    if d["congedo"] != ["qui:a1"]:
        return f"il congedo della copia di amaltea toglie anche quella di qui, o non toglie la sua: {d['congedo']}"
    if d["trova"] != "amaltea":
        return f"trova() prende la riga per sessionId invece che per macchina e id: {d['trova']}"
    if d["stati"] != {"a1": {"stato": "lavora", "host": "amaltea", "doppio": True}}:
        return f"statiCorti non segna l'id doppio: {d['stati']}"
    if d["mic"] != ["studio", "amaltea"]:
        return f"il microfono non segue la macchina dell'etichetta: {d['mic']}"
    m = casa / "mod"
    m.mkdir()
    mod_dati(repo, m, (mod / "dati.js").read_text(encoding="utf-8"))
    (m / "prova.mjs").write_text(PROVA_CHIAVE_DATI, encoding="utf-8")
    app = casa / "app"
    app.mkdir()
    (app / "arturo.json").write_text(json.dumps({"arturo": ["python9", "/a/bin/arturo"], "radice": str(repo), "base": "/base"}), encoding="utf-8")
    herdr = {"panes": [{"terminal": a, "tab": f"tb{a}"} for a in ("t1", "t2", "t3")],
             "terminals": [{"address": "t1", "argv": ["/u/claude", "attach", "a1"]},
                           {"address": "t2", "argv": ["ssh", "-t", *OPZIONI_SSH, "amaltea", "/m/claude", "attach", "a1"]},
                           {"address": "t3", "argv": ["zsh"], "labels": {"arturo.sessione": "a1"}}]}
    e = {**os.environ, "HZ_APP": str(app), "HZ_CASA": str(casa / "casa"), "HZ_SHARED": "{}", "HZ_HERDR": json.dumps(herdr), "HZ_EXEC": "{}"}
    r = subprocess.run([node, str(m / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=30, env=e)
    if r.returncode != 0:
        return f"dati.js non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["la"] != ["t3", "t2"] or d["qui"] != ["t3", "t1"]:
        return f"schedeDi prende la scheda dell'altra copia: qui {d['qui']}, amaltea {d['la']}"
    if d["agganciate"] != {"t1": "qui", "t2": "amaltea"}:
        return f"schedeAgganciate dà a una scheda la copia sbagliata: {d['agganciate']}"
    if d["doppioQui"] != ["t1"] or d["doppioLa"] != ["t2"]:
        return f"con l'id su due macchine l'etichetta vecchia decide ancora: qui {d['doppioQui']}, amaltea {d['doppioLa']}"
    return None

PROVA_COMANDI_CHIAVE = r"""
const S = await import(process.env.HZ_SESSIONI);
const { instrada } = await import(process.env.HZ_COMANDI);
const src = JSON.parse(process.env.HZ_SRC);
const chiave = S.chiave, chiaveSessione = S.chiave;
const avvisi = [];
const notify = (x) => avvisi.push(x.title);
const comandoGesto = eval(src.gesto), comandoSposta = eval(src.sposta);
// i metodi di volta.js su un oggetto finto: vis() è l'elenco mostrato, dati.sessioni tutte le righe
const volta = (vis, tutte) => {
  const o = { vis: () => ({ sessioni: vis }), dati: { sessioni: tutte } };
  o.trovaId = eval("(function " + src.trovaId + ")").bind(o);
  o.vistaId = eval("(function " + src.vistaId + ")").bind(o);
  return o;
};
const host = (s) => (s ? s.host : null);
// dopo Sposta su: a1 c'è qui (ferma) e su amaltea (viva)
const qui = { id: "a1", sessionId: "a1-x", host: "qui", stato: "ferma" };
const la = { id: "a1", sessionId: "c9-y", host: "amaltea", stato: "lavora" };
const mini = { id: "b2", sessionId: "b2-z", host: "torre-tre", stato: "ferma" };
const arg = (c) => instrada(c.slice("arturo.".length)).arg;
const tutte = volta([qui, la], [qui, la]), una = volta([la], [qui, la]), sola = volta([], [qui]);
const r = {
  gesto: [comandoGesto(la, { verbo: "elimina" }), arg(comandoGesto(la, { verbo: "elimina" }))],
  sposta: [comandoSposta("torre-due", la), arg(comandoSposta("torre-due", la)), arg(comandoSposta("torre-due", mini)),
           arg(comandoSposta("amaltea", qui)), instrada("volta-sposta-torre-due-a1b2").arg],
  cambio: S.leggiCambio(S.comandoCambio(la, "nome", "x").slice(7)).id,
  trova: [host(tutte.trovaId("qui:a1")), host(tutte.trovaId("amaltea:a1")), host(una.trovaId("a1")), host(sola.trovaId("a1"))],
};
avvisi.length = 0;
r.nudo = [host(tutte.trovaId("a1")), avvisi.slice()];
avvisi.length = 0;
r.manca = [host(tutte.trovaId("zz")), avvisi.slice()];
r.vista = [host(una.vistaId("qui:a1")), host(una.vistaId("amaltea:a1")), host(una.vistaId("a1"))];
console.log(JSON.stringify(r));
"""


def hz120(repo: Path, casa: Path) -> str | None:
    """I comandi di Volta con la chiave macchina:id (#5643)."""
    mod = repo / "shared/volta/mods/arturo"
    vj = (mod / "volta.js").read_text(encoding="utf-8")
    if "    const prese = l.filter((s) => this.spostaId(macchina, chiave(s), cx, true));" not in vj:
        return "Sposta tutto passa a spostaId il solo id: dopo uno spostamento sta su due macchine"
    node = shutil.which("node")
    if not node:
        return None
    pezzi = {}
    for nome, file, schema in (("gesto", "menusessione.js", r"export const comandoGesto = ([^\n]*);\n"),
                               ("sposta", "sposta.js", r"export const comandoSposta = ([^\n]*);\n"),
                               ("trovaId", "volta.js", r"\n  (trovaId\(id\) \{\n.*?\n  \})\n"),
                               ("vistaId", "volta.js", r"\n  (vistaId\(id\) \{\n.*?\n  \})\n")):
        m = re.search(schema, (mod / file).read_text(encoding="utf-8"), re.S)
        if not m:
            return f"{file}: non trovo {nome}"
        pezzi[nome] = m.group(1)
    shutil.copyfile(mod / "sessioni.js", casa / "sessioni.mjs")
    shutil.copyfile(mod / "comandi.js", casa / "comandi.mjs")
    (casa / "prova.mjs").write_text(PROVA_COMANDI_CHIAVE, encoding="utf-8")
    e = {**os.environ, "HZ_SESSIONI": (casa / "sessioni.mjs").as_uri(), "HZ_COMANDI": (casa / "comandi.mjs").as_uri(), "HZ_SRC": json.dumps(pezzi)}
    r = subprocess.run([node, str(casa / "prova.mjs")], capture_output=True, text=True, encoding="utf-8", timeout=30, env=e)
    if r.returncode != 0:
        return f"la prova dei comandi non gira: {(r.stderr or r.stdout).strip()[-200:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["gesto"] != ["arturo.volta-gesto-elimina-amaltea:a1", {"verbo": "elimina", "id": "amaltea:a1"}]:
        return f"il gesto del menu non porta la chiave macchina:id: {d['gesto']}"
    if d["sposta"] != ["arturo.volta-sposta-amaltea:a1-torre-due", {"macchina": "torre-due", "id": "amaltea:a1"},
                       {"macchina": "torre-due", "id": "torre-tre:b2"}, {"macchina": "amaltea", "id": "qui:a1"},
                       {"macchina": "torre-due", "id": "a1b2"}]:
        return f"Sposta su non porta la chiave, o comandi.js la legge storta: {d['sposta']}"
    if d["cambio"] != "amaltea:a1":
        return f"il cambio di nome o progetto non porta la chiave: {d['cambio']}"
    if d["trova"] != ["qui", "amaltea", "amaltea", "qui"]:
        return f"trovaId non trova la copia della chiave, o non preferisce quella mostrata: {d['trova']}"
    if d["nudo"][0] is not None or not any("due macchine" in a for a in d["nudo"][1]):
        return f"un id nudo su due macchine sceglie una copia a caso: {d['nudo']}"
    if d["manca"][0] is not None or not any("Non trovo" in a for a in d["manca"][1]):
        return f"una sessione che non c'è non dà l'avviso: {d['manca']}"
    if d["vista"] != ["qui", "amaltea", "amaltea"]:
        return f"vistaId non segue la chiave: {d['vista']}"
    return None


PROVE = {"HZ01": hz01, "HZ02": hz02, "HZ03": hz03, "HZ04": hz04, "HZ05": hz05, "HZ06": hz06, "HZ07": hz07, "HZ08": hz08, "HZ09": hz09, "HZ10": hz10, "HZ11": hz11, "HZ12": hz12, "HZ13": hz13, "HZ14": hz14, "HZ15": hz15, "HZ16": hz16, "HZ17": hz17, "HZ18": hz18, "HZ19": hz19, "HZ20": hz20, "HZ21": hz21, "HZ22": hz22, "HZ23": hz23, "HZ24": hz24, "HZ25": hz25, "HZ26": hz26, "HZ27": hz27, "HZ28": hz28, "HZ29": hz29, "HZ30": hz30, "HZ31": hz31, "HZ32": hz32, "HZ33": hz33, "HZ34": hz34, "HZ35": hz35, "HZ36": hz36, "HZ37": hz37, "HZ38": hz38, "HZ39": hz39, "HZ40": hz40, "HZ41": hz41, "HZ42": hz42, "HZ43": hz43, "HZ44": hz44, "HZ45": hz45, "HZ46": hz46, "HZ47": hz47, "HZ48": hz48, "HZ49": hz49, "HZ50": hz50, "HZ51": hz51, "HZ52": hz52, "HZ53": hz53, "HZ54": hz54, "HZ55": hz55, "HZ56": hz56, "HZ57": hz57, "HZ58": hz58, "HZ59": hz59, "HZ60": hz60, "HZ61": hz61, "HZ62": hz62, "HZ63": hz63, "HZ64": hz64, "HZ65": hz65, "HZ66": hz66, "HZ67": hz67, "HZ68": hz68, "HZ69": hz69, "HZ70": hz70, "HZ71": hz71, "HZ72": hz72, "HZ73": hz73, "HZ74": hz74, "HZ75": hz75, "HZ76": hz76, "HZ77": hz77, "HZ78": hz78, "HZ79": hz79, "HZ80": hz80, "HZ81": hz81, "HZ82": hz82, "HZ83": hz83, "HZ84": hz84, "HZ85": hz85, "HZ86": hz86, "HZ87": hz87, "HZ88": hz88, "HZ89": hz89, "HZ90": hz90, "HZ91": hz91, "HZ92": hz92, "HZ93": hz93, "HZ94": hz94, "HZ95": hz95, "HZ96": hz96, "HZ97": hz97, "HZ98": hz98, "HZ99": hz99, "HZ100": hz100, "HZ101": hz101, "HZ102": hz102, "HZ103": hz103, "HZ104": hz104, "HZ105": hz105, "HZ106": hz106, "HZ107": hz107, "HZ108": hz108, "HZ110": hz110, "HZ111": hz111, "HZ113": hz113, "HZ114": hz114, "HZ115": hz115, "HZ116": hz116, "HZ117": hz117, "HZ118": hz118, "HZ119": hz119, "HZ120": hz120}


# I casi che leggono file di Arturo fuori da shared/volta (bin/arturo, hooks/, commands/, settings.json...):
# nel repository di Volta non ci sono, e il caso si salta col motivo. Li trova la lettura del corpo del caso
# (repo / "<fuori da shared/volta>") più i casi con un veleno fuori da shared/volta, più quelli di ALTRI_ARTURO,
# che arrivano ad Arturo da una funzione d'aiuto.
ALTRI_ARTURO: set = {"HZ56"}  # HZ56: il file ORIGINE c'è solo nella copia dentro Arturo


def serve_arturo() -> set:
    import inspect  # noqa: PLC0415
    fuori = re.compile(r"""repo\s*/\s*["'](?!shared/volta)[^"']+["']""")
    casi = {k for k, f in PROVE.items() if fuori.search(inspect.getsource(f))}
    return casi | {v[0] for v in VELENI if not v[1].startswith("shared/volta")} | ALTRI_ARTURO


def senza_arturo(repo: Path) -> bool:
    """Vero se il banco gira senza il repository di Arturo (dal repository di Volta)."""
    return not (repo / "bin" / "arturo").exists()


SALTATI: list = []


def prova(repo: Path, solo: str | None = None) -> list[str]:
    rossi = []
    salta = serve_arturo() if senza_arturo(repo) else set()
    for codice, f in PROVE.items():
        if solo and codice != solo:
            continue
        if codice in salta:
            SALTATI.append(codice)
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
    ('HZ120', 'shared/volta/mods/arturo/comandi.js', '  if (sk) return { verbo: "volta-sposta", arg: { macchina: sk[2], id: sk[1] }, lungo: false };\n', ''),
    ('HZ120', 'shared/volta/mods/arturo/comandi.js', '  const sp = /^volta-sposta-([^:]+)-([0-9A-Za-z]+)$/.exec(c);', '  const sp = null;'),
    ('HZ120', 'shared/volta/mods/arturo/menusessione.js', '${v.verbo}-${chiaveSessione(s)}`;', '${v.verbo}-${s.id}`;'),
    ('HZ120', 'shared/volta/mods/arturo/sposta.js', '`arturo.volta-sposta-${chiave(s)}-${macchina}`;', '`arturo.volta-sposta-${macchina}-${s.id}`;'),
    ('HZ120', 'shared/volta/mods/arturo/volta.js', '    return copie.length === 1 ? l[0] : undefined;', '    return l[0];'),
    ('HZ120', 'shared/volta/mods/arturo/volta.js', '(String(id).includes(":") ? chiave(x) === id : x.id === id', '(x.id === id'),
    ('HZ120', 'shared/volta/mods/arturo/volta.js', '    const prese = l.filter((s) => this.spostaId(macchina, chiave(s), cx, true));', '    const prese = l.filter((s) => this.spostaId(macchina, s.id, cx, true));'),
    ('HZ119', 'shared/volta/mods/arturo/sessioni.js', ' || argv.some((a) => dentro(a, s.id))) && stessoPosto(argv, s);', ' || argv.some((a) => dentro(a, s.id)));'),
    ('HZ119', 'shared/volta/mods/arturo/sessioni.js', '  return ambiguo ? null : true;\n}', '  return true;\n}'),
    ('HZ119', 'shared/volta/mods/arturo/sessioni.js', ' || (Boolean(a.id) && a.id === b.id && (a.host ?? "qui") !== (b.host ?? "qui"));', ';'),
    ('HZ119', 'shared/volta/mods/arturo/sessioni.js', '  const via = chiaviDi(congedi);\n  const l = (dati.sessioni', '  const via = new Set(Object.values(congedi ?? {}).map((c) => c.id));\n  const l = (dati.sessioni'),
    ('HZ119', 'shared/volta/mods/arturo/sessioni.js', 'export const trova = (l, c) => (l ?? []).find((x) => (c?.id ?', 'export const trova = (l, c) => (l ?? []).find((x) => (false ?'),
    ('HZ119', 'shared/volta/mods/arturo/sessioni.js', ', ...(doppio(l, s.id) ? { doppio: true } : {}) };', ' };'),
    ('HZ119', 'shared/volta/mods/arturo/sessioni.js', "    if (x.startsWith(\"-\")) { if (x.length === 2 && OPZIONI_CON_VALORE.has(x[1])) j++; continue; }", "    if (x.startsWith(\"-\")) continue;"),
    ('HZ119', 'shared/volta/mods/arturo/microfono.js', ' && (host === null || (x.host ?? "qui") === host));', ');'),
    ('HZ119', 'shared/volta/mods/arturo/dati.js', 'const ambiguo = (id) => Boolean(shared("arturo.volta.stati")?.[id]?.doppio);', 'const ambiguo = (id) => false;'),
    ('HZ119', 'shared/volta/mods/arturo/dati.js', "    const dice = (y) => etichettaDice(x.labels?.[ETICHETTA], y, doppio(sessioni, y.id));", "    const dice = (y) => (x.labels?.[ETICHETTA] === y.id ? true : null);"),
    ('HZ119', 'shared/volta/mods/arturo/volta.js', '      const s = trova(this.dati?.sessioni, c) ?? undefined;', '      const s = (this.dati?.sessioni ?? []).find((x) => x.sessionId === c.sessionId || (c.id && x.id === c.id));'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '  try { await hc(["label", t.address, `${ETICHETTA}=${chiaveSessione(s)}`]); }', '  try { await hc(["label", t.address, `${ETICHETTA}=${s.id}`]); }'),
    ('HZ118', 'shared/volta/mods/arturo/sessioni.js', '    if (!c || indirizzo === opz.davanti || opz.no?.has(indirizzo)', '    if (!c || opz.no?.has(indirizzo)'),
    ('HZ118', 'shared/volta/mods/arturo/sessioni.js', '    const s = l.find((x) => x.id === c.id && x.host === c.host);', '    const s = l.find((x) => x.id === c.id);'),
    ('HZ118', 'shared/volta/mods/arturo/sessioni.js', ' || s.aspetta || lavoroInCorso(s.coda)) continue;\n    const t = interazione(s);', ' || s.aspetta) continue;\n    const t = interazione(s);'),
    ('HZ118', 'shared/volta/mods/arturo/dati.js', '    if (!agganciata(f.argv, s)) return { errore: "in primo piano non c\'è l\'aggancio di questa sessione" };\n', ''),
    ('HZ118', 'shared/volta/mods/arturo/dati.js', '  return (await nuda(indirizzo)) ? { ok: true } : { errore: "claude attach non si è staccato" };', '  return { ok: true };'),
    ('HZ118', 'shared/volta/mods/arturo/volta.js', ' cx.notify(); this.riaggancia(k, cx); }', ' cx.notify(); }'),
    ('HZ118', 'shared/volta/mods/arturo/volta.js', '    cx.timer.every(OGNI_AUTO, (cx) => this.staccaFerme(cx));\n', ''),
    ('HZ117', 'shared/volta/mods/arturo/volta.js', '    const guasto = this.errore || this.erroreLettura;\n', '    const guasto = this.errore;\n'),
    ('HZ117', 'shared/volta/mods/arturo/volta_sonda.py', '            rc, out, err = lancia([trova_claude(), verbo, sid], timeout=ATTESA_AZIONE)', '            rc, out, err = lancia([shutil.which("claude") or "claude", verbo, sid], timeout=ATTESA_AZIONE)'),
    ('HZ117', 'shared/volta/mods/arturo/volta_sonda.py', 'SERVIZIO = SERVIZIO.replace("#CLAUDE#", CERCA_CLAUDE.strip())\n', ''),
    ('HZ117', 'shared/volta/mods/arturo/sessioni.js', '    if (out[s.id] && out[s.id].stato !== "ferma" && s.stato === "ferma") continue;\n', ''),
    ('HZ117', 'shared/volta/mods/arturo/volta.js', '      risposta = d.errore && !d.stato ? { stato: "errore", motivo: d.errore } : d;', '      risposta = d;'),
    ('HZ117', 'shared/volta/mods/arturo/dati.js', '    try { return await orologio(ms); } catch (e) { orologio = null;', '    try { return await orologio(ms); } catch (e) {'),
    ('HZ117', 'shared/volta/mods/arturo/dati.js', '  if (orologio) {\n    try {', '  if (false) {\n    try {'),
    ('HZ116', 'shared/volta/mods/arturo/dati.js', '  await cambiaVolo((d) => { d[nomeSposta(s)] = { ...v, preso: Date.now() }; });\n', ''),
    ('HZ116', 'shared/volta/mods/arturo/dati.js', '    await togliVolo(k);\n    return x;', '    return x;'),
    ('HZ116', 'shared/volta/mods/arturo/dati.js', '    if (chiuse && Array.isArray(s.attach) && s.attach.length) riaperta = await apriSessione(s, s.attach)', '    if (false) riaperta = await apriSessione(s, s.attach)'),
    ('HZ116', 'shared/volta/mods/arturo/sessioni.js', '  if (ora - v.dal > VOLO_MAX_MS) return "scarta";\n', ''),
    ('HZ116', 'shared/volta/mods/arturo/sessioni.js', '? "altrui" : "mia";', '? "mia" : "mia";'),
    ('HZ116', 'shared/volta/mods/arturo/volta.js', '      this.riprendiVolo(cx);\n', ''),
    ('HZ113', 'shared/volta/mods/arturo/sessioni.js', '  return { chiave: n?.chiave ?? k, titolo: n?.titolo ?? null };', '  return { chiave: k, titolo: n?.titolo ?? null };'),
    ('HZ113', 'shared/volta/mods/arturo/sessioni.js', 'export const chiaveProgetto = (p) => progettoDi(p).chiave;', 'export const chiaveProgetto = (p) => String(p ?? "");'),
    ('HZ113', 'shared/volta/mods/arturo/dati.js', 'export const canonico = (nome) => progettoDi(nome, shared("arturo.progetti")).chiave;', 'export const canonico = (nome) => slug(nome);'),
    ('HZ113', 'shared/volta/mods/arturo/dati.js', '  const nomeSpazio = s.progetto ? canonico(s.progetto) : SPAZIO_LIBERO;', '  const nomeSpazio = s.progetto ? slug(s.progetto) : SPAZIO_LIBERO;'),
    ('HZ113', 'shared/volta/mods/arturo/dati.js', '  const sp = s.progetto ? spazio(nomeSpazio) :', '  const sp = s.progetto ? spaces().find((x) => !x.machine && slug(x.name) === nomeSpazio) :'),
    ('HZ113', 'shared/volta/mods/arturo/dati.js', ' && !libero(s.name) && progettoDi(s.name, m).chiave === k) : undefined;', ' && progettoDi(s.name, m).chiave === k) : undefined;'),
    ('HZ113', 'shared/volta/mods/arturo/testata.js', 'progettoDi(s.name, shared("arturo.progetti")).titolo ?? s.name', 'shared("arturo.progetti")?.[s.name]?.titolo ?? s.name'),
    ('HZ114', 'shared/volta/mods/arturo/volta_sonda.py', '    return nome_qui() if nome in (None, "", "qui") else nome', '    return nome or "questa macchina"'),
    ('HZ114', 'shared/volta/mods/arturo/sessioni.js', 'export const nomeMacchina = (m, macchine) => (m === "qui" ? macchinaQui(macchine) ?? "questa macchina" : m);', 'export const nomeMacchina = (m, macchine) => (m === "qui" ? "questa macchina" : m);'),
    ('HZ114', 'shared/volta/mods/arturo/sessioni.js', '.find((x) => x?.questa)?.macchina ?? null;', '[0]?.host ?? null;'),
    ('HZ114', 'shared/volta/mods/arturo/dati.js', 'export const nomeMacchina = (m) => nomeMacchinaDi(m, shared("arturo.volta.macchine"));', 'export const nomeMacchina = (m) => nomeMacchinaDi(m, []);'),
    ('HZ114', 'shared/volta/mods/arturo/dati.js', '    return dico(`La sessione non nasce su ${nomeMacchina(macchina)}`, nata.errore ?? "nessuna risposta");', '    return dico(`La sessione non nasce su ${macchina}`, nata.errore ?? "nessuna risposta");'),
    ('HZ115', 'shared/volta/mods/arturo/volta_sonda.py', 'sys.dont_write_bytecode = True\n', ''),
    ('HZ115', 'shared/volta/mods/arturo/volta_note.py', 'sys.dont_write_bytecode = True\n', ''),
    ('HZ111', 'shared/volta/mods/arturo/volta_sposta.py', '    if f and not os.environ.get("VOLTA_SPOSTA_FIGLIO"):', '    if False:'),
    ('HZ111', 'shared/volta/mods/arturo/volta_sposta.py', '    if f:\n        scrivi_esito(f, dict(esito, finito=True))', '    if f and "errore" not in esito:\n        scrivi_esito(f, dict(esito, finito=True))'),
    ('HZ111', 'shared/volta/mods/arturo/sessioni.js', 'export const SPOSTA_MAX_MS = 25 * 60000,', 'export const SPOSTA_MAX_MS = 9 * 60000,'),
    ('HZ111', 'shared/volta/mods/arturo/sessioni.js', '  if (d && typeof d === "object" && d.finito === true) { const { finito: _, ...resto } = d; return { fatto: resto }; }', '  if (d && typeof d === "object") return { fatto: d };'),
    ('HZ111', 'shared/volta/mods/arturo/volta.js', 'r = await spostaSessione(s, v.macchina, (ms) => cx.sleep(ms));', 'r = await spostaSessione(s, v.macchina);'),
    ('HZ110', 'shared/volta/mods/arturo/sessioni.js', '  return (percorsi ?? []).some((p) => { const x = n(p); return x === c || x === f; });', '  return (percorsi ?? []).length > 0;'),
    ('HZ110', 'shared/volta/mods/arturo/sessioni.js', '  if (v.appeso) return ora - v.appeso < ARTURO_PAUSA_MS ? { fai: "appeso" } : { fai: "lancia" };', '  if (v.appeso) return { fai: "lancia" };'),
    ('HZ110', 'shared/volta/mods/arturo/sessioni.js', '  return ora - v.da < tetto ? { fai: "aspetta" } : { fai: "appeso" };', '  return { fai: "lancia" };'),
    ('HZ110', 'shared/volta/mods/arturo/dati.js', '  if (passo.fai === "aspetta") return voli[chiave].p;\n', ''),
    ('HZ108', 'shared/volta/mods/arturo/sessioni.js', '    else if (s.stato === "errore") out.push({ s, fai: "rm", avviso:', '    else out.push({ s, fai: "rm", avviso:'),
    ('HZ106', 'shared/volta/mods/arturo/volta_sonda.py', '    if any(x > crash[-1][0] for x in nati):\n        return None', '    if False:\n        return None'),
    ('HZ106', 'shared/volta/mods/arturo/volta_sonda.py', '> NASCITE_MIN * 60:', '> NASCITE_MIN * 6000:'),
    ('HZ106', 'shared/volta/mods/arturo/volta_sonda.py', '            s["congedo"] = True', '            pass'),
    ('HZ106', 'shared/volta/mods/arturo/volta_sonda.py', '            voce["nascita"] = v["nascita"]', '            pass'),
    ('HZ107', 'shared/volta/mods/arturo/sessioni.js', 'return n ? { riparte: false, errore: avvisoNascita(n) } : { riparte: true };', 'return { riparte: true };'),
    ('HZ107', 'shared/volta/mods/arturo/sessioni.js', 'if (!viste?.[k]) avvisi.push', 'avvisi.push'),
    ('HZ107', 'shared/volta/mods/arturo/dati.js', '  if (rc.errore) return { errore: rc.errore };\n', ''),
    ('HZ107', 'shared/volta/mods/arturo/dati.js', '{ cwd: c.base, timeout: ARTURO_MAX_MS }', '{ cwd: c.base }'),
    ('HZ108', 'shared/volta/mods/arturo/sessioni.js', 'if (!morta) { if (s.fineFatta) out.push({ s, fai: "stop" }); }', 'if (!morta) out.push({ s, fai: "stop" });'),
    ('HZ108', 'shared/volta/mods/arturo/sessioni.js', 'ora - tempo(s) < CONGEDO_ORFANO_MS) continue;', 'ora - tempo(s) < 0) continue;'),
    ('HZ108', 'shared/volta/mods/arturo/sessioni.js', '    if (!morta && conScheda.has(chiave(s))) continue;', '    if (conScheda.has(chiave(s))) continue;'),
    ('HZ108', 'shared/volta/mods/arturo/volta.js', '        this.orfaniNo.add(chiave(p.s));\n', ''),
    ('HZ104', 'shared/volta/mods/arturo/sessioni.js', '  && s.stato !== "errore" && !nonSiSposta(s) &&', '  && !nonSiSposta(s) &&'),
    ('HZ104', 'shared/volta/mods/arturo/sessioni.js', '  if (s.tipo === "background") out.push({ verbo: "sposta", testo: "Sposta su…" });\n', ''),
    ('HZ104', 'shared/volta/mods/arturo/sessioni.js', '  return null;\n}\n\n// Una sessione che sta facendo un turno', '  if (s.stato === "lavora") return "Sta lavorando.";\n  return null;\n}\n\n// Una sessione che sta facendo un turno'),
    ('HZ104', 'shared/volta/mods/arturo/comandi.js', '  if (c.startsWith("volta-spostatutto-")) return { verbo: "volta-spostatutto", arg: dopo("volta-spostatutto-"), lungo: false };\n', ''),
    ('HZ104', 'shared/volta/mods/arturo/volta_sposta.py', '    occupata = lavora(da, sid)\n    if occupata:\n        return occupata\n    # Da qui', '    # Da qui'),
    ('HZ104', 'shared/volta/mods/arturo/volta_sposta.py', '    occupata = lavora(da, sid)\n    if occupata:\n        return occupata\n    letto', '    letto'),
    ('HZ104', 'shared/volta/mods/arturo/volta.js', '      this.passiCongedo(cx);\n      this.giraCoda(cx);', '      this.passiCongedo(cx);'),
    ('HZ104', 'shared/volta/mods/arturo/volta_sposta.py', '        if ora.get("errore") or ora.get("pid"):\n', '        if False:\n'),
    ('HZ104', 'shared/volta/mods/arturo/volta_sposta.py', '    if fermata.get("errore"):\n', '    if False:\n'),
    ("HZ103", "shared/volta/mods/arturo/sessioni.js", "export const MOSSA_PX = 6;", "export const MOSSA_PX = 0;"),
    ("HZ103", "shared/volta/mods/arturo/sessioni.js", "Math.hypot(a.x - da.x, a.y - da.y) >= MOSSA_PX", "Math.hypot(a.x - da.x, a.y - da.y) > 99"),
    ("HZ103", "shared/volta/mods/arturo/sessioni.js", "  if (chiaveProgetto(t.s.progetto) === g.chiave) return null;\n", ""),
    ("HZ103", "shared/volta/mods/arturo/sessioni.js", "if (!t?.s || !t.mosso || t.s.vecchia || modo !== \"progetto\" || !g?.chiave) return null;", "if (!t?.s || !g?.chiave) return null;"),
    ("HZ103", "shared/volta/mods/arturo/sessioni.js", "  return progettoNuovo(g.chiave) || null;", "  return g.chiave || null;"),
    ("HZ103", "shared/volta/mods/arturo/volta.js", 'if (arrivo) this.cambia(tr.s, "progetto", arrivo, cx);', ""),
    ("HZ103", "shared/volta/mods/arturo/volta.js", "if (this.trascino?.mosso || Date.now() - this.trascinata < 500) return;", ""),
    ("HZ103", "shared/volta/mods/arturo/volta.js", '.on_mouse_down("left", (e) => { if (modo === "progetto") this.trascino', '.on_mouse_down("left", (e) => { if (true) this.trascino'),
    ('HZ96', 'shared/volta/layouts/arturo.json', '"active": "main"', '"active": "casa"'),
    ('HZ96', 'shared/volta/mods/arturo/barra.js', '    terminale();\n    this.carica(cx);', '    this.carica(cx);'),
    ('HZ96', 'shared/volta/mods/arturo/barra.js', ' setShared("arturo.casa.apri", Date.now()); }', ' }'),
    ('HZ96', 'shared/volta/mods/arturo/casa.js', '    this.leggiImmagini(cx);\n    cx.timer.every(60000', '    terminale();\n    this.leggiImmagini(cx);\n    cx.timer.every(60000'),
    ('HZ96', 'shared/volta/mods/arturo/tessere.js', '  if (!q) return [NUOVA, ...l];', '  if (!q) return l;'),
    ('HZ96', 'shared/volta/mods/arturo/tessere.js', '  return [...l.filter(inizia), ...l.filter((p) => !inizia(p) && testo(p).includes(q))];', '  return l.filter((p) => testo(p).includes(q));'),
    ('HZ96', 'shared/volta/mods/arturo/tessere.js', '  if (dopo >= n) return tasto === "down" ? at : n - 1;', '  if (dopo >= n) return dopo % n;'),
    ('HZ96', 'shared/volta/mods/arturo/tessere.js', 'Math.floor(((Number(w) || 0) + GAP) / (MIN_W + GAP))', 'Math.ceil(((Number(w) || 0) + GAP) / (MIN_W + GAP))'),
    ('HZ96', 'shared/volta/mods/arturo/tessere.js', 'arrivate instanceof Set && arrivate.has(chiave)', 'arrivate instanceof Set'),
    ('HZ96', 'shared/volta/mods/arturo/comandi.js', '  if (c === "casa" || c === "casa-chiudi") return { verbo: c, arg: null, lungo: false };\n', ''),
    # #5456: tasto della macchina, guida, note sulle tessere, layout senza tessere
    ('HZ96', 'shared/volta/mods/arturo/tessere.js', 'export const senzaTessere = (lay) => Boolean(lay) && !haTessere(lay);', 'export const senzaTessere = (lay) => !haTessere(lay);'),
    ('HZ96', 'shared/volta/mods/arturo/tessere.js', 'export const tessereMostrate = (lay) => haTessere(lay) && nodo(lay, STACK).active === CASA;', 'export const tessereMostrate = (lay) => haTessere(lay);'),
    ('HZ96', 'shared/volta/mods/arturo/nota.js', '    tessere: trova(lay, "lavoro")?.active === "casa" };', '    tessere: false };'),
    ('HZ96', 'shared/volta/mods/arturo/nota.js', 'benvenuto: "benvenuto", casa: "tessere" };', 'benvenuto: "benvenuto" };'),
    ('HZ96', 'shared/volta/mods/arturo/barra.js', '    else if (c === "casa" && senzaTessere(layout())) this.lungo("volta-nuova", cx, () => nuovaScheda());\n', ''),
    ('HZ96', 'shared/volta/mods/arturo/casa.js', '{ if (!senzaTessere(layout())) run("layout.select"', '{ run("layout.select"'),
    ('HZ96', 'shared/volta/mods/arturo/comuni.js', 'tessere: "Ctrl+Shift+T" }', 'tessere: "⌘T" }'),
    ('HZ96', 'shared/volta/mods/arturo/guida.js', '${tasti().tessere} mostra le tessere dei progetti', 'Altra conversazione mostra le tessere dei progetti'),
    ('HZ96', 'shared/volta/mods/arturo/main.js', '"benvenuto", "casa"]);', '"benvenuto"]);'),
    ('HZ97', 'shared/volta/mods/arturo/volta_note.py', 'from volta_sonda import errore_hc, hc, leggi_json,', 'from volta_sonda import errore_hc, hc_vecchio as hc, leggi_json,'),
    ('HZ97', 'shared/volta/mods/arturo/volta.js', '`${cacheVolta("volta-note")}/stato.json`', '`${cacheVolta()}/note.json`'),
    ('HZ97', 'shared/volta/mods/arturo/volta.js', '      cx.notify();\n      this.sincronizzaNote(cx);', '      cx.notify();'),
    ('HZ94', 'shared/volta/mods/arturo/sessioni.js', '.map(chiave).filter((k) => !viste.has(k));', '.map(chiave);'),
    ('HZ94', 'shared/volta/mods/arturo/sessioni.js', 'export const ESCE = { duration: 140, easing: "ease-in" };', 'export const ESCE = { duration: 400, easing: "ease-in" };'),
    ('HZ94', 'shared/volta/mods/arturo/comuni.js', 'svg("mods/arturo/stella-lavora.svg").size(d + 4).flex_none().text_color(colore));', 'svg("mods/arturo/stella-lavora.svg").size(d + 4).flex_none().text_color(colore).spin(GIRO_MS));'),
    ('HZ94', 'shared/volta/mods/arturo/barra.js', '      .child(stella)', '      .child(stella.loop("opacity", { from: 0.3, to: 1, period: 1100 }))'),
    ('HZ94', 'shared/volta/mods/arturo/volta.js', 'if (!c.uscita && this.esce(s, c, cx)) return;', 'if (this.esce(s, c, cx)) return;'),
    ('HZ94', 'shared/volta/mods/arturo/volta.js', '    if (!movimento()) return false;\n    const k = chiave(s);', '    const k = chiave(s);'),
    ('HZ92', 'shared/volta/mods/arturo/sessioni.js', '  if (s.chi !== "claude" || chiede(s.coda)) return "stasi";', '  if (chiede(s.coda)) return "stasi";'),
    ('HZ92', 'shared/volta/mods/arturo/sessioni.js', '  /\\b(scrivimi|scrivi|dimmi|', '  /\\b(xscrivimi|xscrivi|dimmi|'),
    ('HZ92', 'shared/volta/mods/arturo/sessioni.js', '  /prossimo passo:[^\\n]*(\\btu\\b|\\btuo\\b|\\btua\\b|\\bfederico\\b|\\(tu\\))/i,\n', ''),
    ('HZ92', 'shared/volta/mods/arturo/sessioni.js', '  /\\?[\\s*_`)]*$/,\n  /\\?\\s*\\n/,\n', ''),
    ('HZ92', 'shared/volta/mods/arturo/sessioni.js', '  if (s.stato === "aspetta" || s.aspetta) return "stasi";', '  if (s.stato === "aspetta") return "stasi";'),
    ('HZ92', 'shared/volta/mods/arturo/sessioni.js', '  const vive = g.sessioni.filter((s) => !inAttesa(s));', '  const vive = g.sessioni.filter((s) => s.stato !== "ferma");'),
    ('HZ92', 'shared/volta/mods/arturo/sessioni.js', '  if (f === "stasi") return { testo: (q ? `Ti aspetta ${q}` : "Ti aspetta") + zz, colore: "blocked" };\n', ''),
    ('HZ92', 'shared/volta/mods/arturo/volta_sonda.py', '                    chi, interazione = "claude", d.get("timestamp", interazione)', '                    chi = "claude"'),
    ('HZ92', 'shared/volta/mods/arturo/volta_sonda.py', '            fine_fatta = bool(re.match(', '            fine_fatta = False and bool(re.match('),
    ('HZ92', 'shared/volta/mods/arturo/volta_sonda.py', '"chi": s.get("chi") or "", "fineFatta": s.get("fineFatta") is True,', '"chi": s.get("chi") or "",'),
    ('HZ93', 'shared/volta/mods/arturo/sessioni.js', ' && fase(s) === "attesa" && !lavoroInCorso(s.coda))', ' && fase(s) === "attesa")'),
    ('HZ93', 'shared/volta/mods/arturo/sessioni.js', ' && !scheda.has(chiave(s)))', ')'),
    ('HZ93', 'shared/volta/mods/arturo/sessioni.js', '.filter((s) => s.questa && s.tipo === "background" && !s.vecchia', '.filter((s) => s.tipo === "background" && !s.vecchia'),
    ('HZ93', 'shared/volta/mods/arturo/sessioni.js', '    .sort((a, b) => interazione(a) - interazione(b));', '    .sort((a, b) => interazione(b) - interazione(a));'),
    ('HZ93', 'shared/volta/mods/arturo/sessioni.js', '  return Math.max(0, Math.min((opz.ora ?? 3) - ora,', '  return Math.max(0, Math.min((opz.ora ?? 4) - ora,'),
    ('HZ93', 'shared/volta/mods/arturo/sessioni.js', '      vista: v?.vista ?? adesso, ultima: adesso });', '      vista: adesso, ultima: adesso });'),
    ('HZ93', 'shared/volta/mods/arturo/sessioni.js', '    if (c.fineFatta && s.stato !== "lavora") return { fai: "stop", fase: "ferma", salvata: true };\n', ''),
    ('HZ93', 'shared/volta/mods/arturo/volta.js', '      if (cfg.modo === "prova") {', '      if (cfg.modo === "provaX") {'),
    ('HZ93', 'shared/volta/mods/arturo/volta.js', '        await writeTextFile(file, JSON.stringify({ ...reg, modo: "prova", prova }, null, 1), testo);\n        return;', '        await writeTextFile(file, JSON.stringify({ ...reg, modo: "prova", prova }, null, 1), testo);\n        this.congeda({ sessionId: scelte[0].sessionId, auto: true }, cx);\n        return;'),
    ('HZ93', 'shared/volta/mods/arturo/volta.js', '      if (!scelte.length || restanti(fatti, adesso, cfg) < 1) return;', '      if (!scelte.length) return;'),
    ('HZ93', 'shared/volta/mods/arturo/volta.js', 'chiuse: [...(reg.chiuse ?? []).slice(-39), { sessionId: s.sessionId, titolo: titolo(s), quando: adesso, interazione: s.interazione || s.ultimo || "" }] }, null, 1), testo);', 'chiuse: [...(reg.chiuse ?? []).slice(-39), { sessionId: s.sessionId, titolo: titolo(s), quando: adesso, interazione: s.interazione || s.ultimo || "" }] }, null, 1), null);'),
    ('HZ93', 'shared/volta/mods/arturo/dati.js', 'modo: ["prova", "acceso", "spento"].includes(c.congedo) ? c.congedo : "prova",', 'modo: ["prova", "acceso", "spento"].includes(c.congedo) ? c.congedo : "acceso",'),
    ('HZ93', 'shared/volta/mods/arturo/volta_sonda.py', 'PROMPT_CONGEDO_AUTO if auto else PROMPT_CONGEDO', 'PROMPT_CONGEDO'),
    ("HZ88", "shared/volta/themes/arturo.json", '"#7f90a8"', '"#4a5568"'),
    ("HZ88", "shared/volta/themes/arturo.json", '"selection": "#1f4478"', '"selection": "#9fb4d0"'),
    ("HZ88", "shared/volta/themes/arturo-carta.json", '"#6b717a"', '"#8a9099"'),
    ("HZ88", "shared/volta/layouts/arturo.json", '"color": "ring"', '"color": "#2f6fe0"'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', '            if processo(a["riprendi"]):\n                break\n        else:\n            continue', '            break\n        else:\n            continue'),
    ('HZ90', 'shared/volta/mods/arturo/sessioni.js', '.replace(/\\s*\\([^)]*\\)\\s*$/, "")', '.replace(/\\s*\\(x\\)\\s*$/, "")'),
    ('HZ90', 'shared/volta/mods/arturo/sessioni.js', '  const dove = modo === "progetto" ? macchinaBreve(s.macchina) :', '  const dove = modo === "progetto" ? s.macchina :'),
    ('HZ90', 'shared/volta/mods/arturo/testata.js', '      .child(bottone("dafare"', '      .child(bottone("altra", "plus", "Altra conversazione", () => run("arturo.volta-nuova")))\n      .child(bottone("dafare"'),
    ('HZ90', 'shared/volta/mods/arturo/testata.js', '    const macchina = tab ? (dv?.schede?.[term] ?? dv?.qui ?? null) : null;', '    const macchina = null;'),
    ('HZ90', 'shared/volta/mods/arturo/volta.js', '(el) => el.on_click(() => apriProgetto(g.chiave))\n', '(el) => el\n'),
    ('HZ91', 'shared/volta/mods/arturo/sessioni.js', '  if (noto) return noto;', ''),
    ('HZ91', 'shared/volta/mods/arturo/sessioni.js', '    for (const s of righe) metti(chiaveProgetto(s.progetto), nomeProgetto(s.progetto), s);', '    for (const s of righe) metti(s.progetto ? String(s.progetto) : "", nomeProgetto(s.progetto), s);'),
    ('HZ91', 'shared/volta/mods/arturo/sessioni.js', '  const nomi = (p) => [p, slugDi(nomeProgetto(p))];', '  const nomi = (p) => [p];'),
    ('HZ91', 'shared/volta/mods/arturo/dati.js', ' if (m.titolo) v.titolo = m.titolo; continue; }', ' continue; }'),
    ('HZ89', 'shared/volta/mods/arturo/sessioni.js', 'const l = (dati.sessioni ?? []).filter((s) => !chiusa(s) && !via.has(chiave(s)));', 'const l = (dati.sessioni ?? []).filter((s) => !via.has(chiave(s)));'),
    ('HZ89', 'shared/volta/mods/arturo/sessioni.js', "    if (ind in (adesso ?? {}) || (tolti?.[ind] && ora - tolti[ind] < TOLTI_MS) || !s?.id || viste.has(chiave(s))) continue;", "    if (ind in (adesso ?? {}) || !s?.id || viste.has(chiave(s))) continue;"),
    ('HZ89', 'shared/volta/mods/arturo/sessioni.js', '    if (s.stato === "lavora" && ora - da < CONGEDO_MAX_MS) return { fai: "attendi" };', '    if (s.stato === "lavora" && ora - da < 1) return { fai: "attendi" };'),
    ('HZ89', 'shared/volta/mods/arturo/sessioni.js', '    if (s.stato === "aspetta") return { fai: "stop", fase: "ferma", avviso:', '    if (s.stato === "aspetta") return { fai: "attendi", fase: "ferma", avviso:'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', '    argv += ["--resume", a["riprendi"]] + ([] if a.get("stessa") else ["--fork-session"])', '    argv += ["--resume", a["riprendi"], "--fork-session"]'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', '"chiusa": senza and (s.get("state") == "stopped" or s.get("fineFatta") is True or s.get("spostata") is True),', '"chiusa": senza and (s.get("state") == "stopped" or s.get("fineFatta") is True),'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sposta.py', '    d.pop("spostata", None)\n', '    pass\n'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sposta.py', '    esegui(da, SEGNA, {"sid": sid, "spostata": a or "qui"})', '    pass'),
    ('HZ89', 'shared/volta/mods/arturo/dati.js', '  const chiuse = chiudiSchede(s);', '  const chiuse = 0;'),
    ('HZ89', 'shared/volta/mods/arturo/dati.js', 'const x = await fineSposta(s, macchina, p.errore ? { errore: p.errore } : p.fatto, v.chiuse);', 'const x = p.errore ? { errore: p.errore } : await fineSposta(s, macchina, p.fatto, v.chiuse);'),
    ('HZ89', 'shared/volta/mods/arturo/volta.js', '    const l = [this.vis()?.sessioni, this.dati?.sessioni].map(tra).find((x) => x.length) ?? [];', '    const l = [this.dati?.sessioni].map(tra).find((x) => x.length) ?? [];'),
    ('HZ89', 'shared/volta/mods/arturo/dati.js', ' &&\n    !(tolti[x.address] && Date.now() - tolti[x.address] < TOLTI_MS));', ');'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', '    fermata = azione(nome, "stop", sid_lavoro)', '    fermata = {}'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', '    ferma = azione(nome, "stop", sid_lavoro)  # già ferma', '    ferma = {}  # già ferma'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', 'r = nasci(nome, "/inizio %s" % slug, None, cartella, riprendi=session_id, stessa=True)', 'r = nasci(nome, "/inizio %s" % slug, None, cartella, riprendi=session_id)'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', '    if argv and argv[0] == "inizia":\n', '    if False:\n'),
    ('HZ89', 'shared/volta/mods/arturo/volta_sonda.py', '"chiusa": senza and (s.get("state") == "stopped" or s.get("fineFatta") is True or s.get("spostata") is True),', '"chiusa": False,'),
    ('HZ89', 'shared/volta/mods/arturo/volta.js', '    chiudiSchede(s);\n    this.congeda(s, cx);', '    chiudiSchede(s);\n    azioneSessione(s, "stop");'),
    ('HZ89', 'shared/volta/mods/arturo/dati.js', '    segnaTolto(t.address);\n    // confirmed:', '    // confirmed:'),
    ('HZ87', 'shared/volta/mods/arturo/dati.js', 'const l = terminals().filter((x) => visti.has(x.address) && !String(x.address).includes("/") && !occupataDaAltra(x, s) &&', 'const l = terminals().filter((x) => visti.has(x.address) && !occupataDaAltra(x, s) &&'),
    ('HZ87', 'shared/volta/mods/arturo/dati.js', '  if (riavviata || m?.fermo) return fallita(m);', '  if (riavviata) return fallita(m);'),
    ('HZ87', 'shared/volta/mods/arturo/dati.js', '  if (riavviata || m?.fermo) return fallita(m);', '  if (riavviata || m) return fallita(m);'),
    ('HZ87', 'shared/volta/mods/arturo/dati.js', '({ errore: m?.testo ?? "Claude non resta aperto', '({ errore: "Claude non resta aperto'),
    ('HZ87', 'shared/volta/mods/arturo/dati.js', '    return r.code === 0 ? motivoUscita(r.stdout, s) : null;', '    return null;'),
    ('HZ87', 'shared/volta/mods/arturo/dati.js', 'fallita((await perche(s, indirizzo)) ?? m)', 'fallita(null)'),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', '  righe.forEach((r, i) => { if (/[%$#>]\\s.*\\battach[\'"]?\\s+[\'"]?[\\w-]{4,}/.test(r)) da = i; });\n', ''),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', 'return { testo: frase(m), fermo: true };', 'return { testo: frase(m), fermo: false };'),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', '  const m = s?.questa ? "questa macchina" : (s?.macchina', '  const m = !s?.questa ? "questa macchina" : (s?.macchina'),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', '  if (/before init/.test(perche)) return', '  if (false) return'),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', 'Claude esce appena parte (${perche}).`, fermo: false };', 'Claude esce appena parte (${perche}).`, fermo: true };'),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', '  [/No job matching/, (m)', '  [/No job matchingX/, (m)'),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', '.replace(/\\u001b\\[[0-9;?]*[A-Za-z]/g, "").split("\\n");', '.split("\\n");'),
    ('HZ87', 'shared/volta/mods/arturo/sessioni.js', '  if (perche) return { testo:', '  if (false) return { testo:'),
    ("HZ86", "shared/volta/keys.json", '"cmd-down": "arturo.volta-giro-avanti"', '"cmd-down": "agent.next"'),
    ("HZ86", "shared/volta/mods/arturo/barra.js", 'else if (c === "volta-giro") this.volta.giro(arg, cx);', ""),
    ("HZ86", "shared/volta/mods/arturo/comandi.js", 'return { verbo: "volta-giro", arg: c.endsWith("avanti") ? 1 : -1, lungo: false };', 'return { verbo: "volta-giro", arg: 1, lungo: false };'),
    ("HZ86", "shared/volta/mods/arturo/sessioni.js", '.filter((s) => ["aggancia", "mostra"].includes(clic(s).azione)).map(chiave);', '.map(chiave);'),
    ("HZ86", "shared/volta/mods/arturo/sessioni.js", "const tiene = prima && ora - prima.quando <= GIRO_MS;", "const tiene = Boolean(prima);"),
    ("HZ86", "shared/volta/mods/arturo/sessioni.js", "  return ids[(i + (verso < 0 ? -1 : 1) + ids.length) % ids.length];", "  return ids[Math.min(ids.length - 1, Math.max(0, i + (verso < 0 ? -1 : 1)))];"),
    ("HZ86", "shared/volta/mods/arturo/sessioni.js", "    return vista.concat(g.sessioni.filter((s) => !vista.includes(s)));", "    return vista;"),
    ("HZ86", "shared/volta/mods/arturo/sessioni.js", '    .filter((s) => s.stato !== "ferma" || !s.fineFatta || conScheda.has(chiave(s)))\n', ""),
    ("HZ86", "shared/volta/mods/arturo/sessioni.js", '.filter((s) => s.stato !== "ferma" || !s.fineFatta || conScheda.has(chiave(s)))', '.filter((s) => s.stato !== "ferma" || conScheda.has(chiave(s)))'),
    ("HZ22", "shared/volta/keys-ctrl.json", '"ctrl-w": "arturo.volta-chiudi"', '"ctrl-w": "tab.close"'),
    ("HZ86", "shared/volta/mods/arturo/volta.js", "    if (s) { this.scopri(s); this.premi(s, cx); }", "    if (s) this.premi(s, cx);"),
    ("HZ86", "shared/volta/mods/arturo/sessioni.js", '  return occupanti(l)[terminale.address]\n    ?? l.find(', '  return l.find('),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '  return t ? t[0].toUpperCase() + t.slice(1) : SENZA;', '  return t[0].toUpperCase() + t.slice(1);'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '  return ultimo ? piatto(m[1]) === piatto(ultimo) : true;', '  return true;'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '  return ultimo ? piatto(m[1]) === piatto(ultimo) : true;', '  return ultimo ? m[1] === ultimo : true;'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '  return ultimo ? piatto(m[1]) === piatto(ultimo) : true;', '  return ultimo ? piatto(m[1]) === piatto(ultimo) : false;'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '.split(/[\\\\/]+/).filter(Boolean).pop();', '.split(/[/]+/).filter(Boolean).pop();'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '.split(/[\\\\/]+/).filter(Boolean).pop();', '.split(/[\\\\/]+/).pop();'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '  if (!nome || nome === s.id) return true;', '  if (!nome) return true;'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '  if (!nome || nome === s.id) return true;', '  if (nome === s.id) return true;'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', '  if (!nomeAutomatico(s)) return nome;', '  if (nome) return nome;'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', 'const piatto = (x) => String(x ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");', 'const piatto = (x) => String(x ?? "").replace(/[^a-z0-9]/g, "");'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', 'const piatto = (x) => String(x ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");', 'const piatto = (x) => String(x ?? "").toLowerCase();'),
    ('HZ83', 'shared/volta/mods/arturo/sessioni.js', 'const m = /^([\\w.-]+)-[0-9a-f]{2}$/.exec(nome);', 'const m = /^([\\w.-]+)-\\w{2}$/.exec(nome);'),
    ('HZ84', 'shared/volta/mods/arturo/dati.js', 'export const eProgetto = (s) => Boolean(s) && !s.machine && Boolean(s.named) && !libero(s.name);', 'export const eProgetto = (s) => Boolean(s) && !s.machine && Boolean(s.named);'),
    ('HZ84', 'shared/volta/mods/arturo/dati.js', 'export const eProgetto = (s) => Boolean(s) && !s.machine && Boolean(s.named) && !libero(s.name);', 'export const eProgetto = (s) => Boolean(s) && Boolean(s.named) && !libero(s.name);'),
    ('HZ84', 'shared/volta/mods/arturo/dati.js', 'export const eProgetto = (s) => Boolean(s) && !s.machine && Boolean(s.named) && !libero(s.name);', 'export const eProgetto = (s) => Boolean(s) && !s.machine && !libero(s.name);'),
    ('HZ84', 'shared/volta/mods/arturo/dati.js', 'export const libero = (nome) => ["senza-progetto", "volta"].includes(slug(nome));', 'export const libero = (nome) => ["senza-progetto", "volta"].includes(nome);'),
    ('HZ84', 'shared/volta/mods/arturo/dati.js', '    if (!eProgetto(s)) continue;', '    if (s.machine || !s.named) continue;'),
    ('HZ84', 'shared/volta/mods/arturo/todo.js', '    return eProgetto(s) ? slug(s.name) : null;', '    return s && !s.machine && s.named ? slug(s.name) : null;'),
    ('HZ84', 'shared/volta/mods/arturo/barra.js', 'this.lungo(c, cx, () => nuovaScheda());', 'this.lungo(c, cx, () => nuova(""));'),
    ('HZ85', 'shared/volta/mods/arturo/todo.js', 'this.fatti = ancoraFatti(this.fatti, r.json);', 'this.fatti.clear();'),
    ('HZ85', 'shared/volta/mods/arturo/todo.js', 'this.fatti = ancoraFatti(this.fatti, r.json);', ''),
    ('HZ85', 'shared/volta/mods/arturo/todo.js', '      setShared("arturo.scritto", Date.now());\n      if (r.ok) notify(', '      if (r.ok) notify('),
    ('HZ85', 'shared/volta/mods/arturo/azioni.js', '.filter((id) => vivi.has(id)));', ');'),
    ('HZ85', 'shared/volta/mods/arturo/azioni.js', '  return new Set([...(fatti ?? [])].filter((id) => vivi.has(id)));', '  return new Set();'),
    ('HZ85', 'shared/volta/mods/arturo/azioni.js', '  return new Set([...(fatti ?? [])].filter((id) => vivi.has(id)));', '  for (const id of fatti ?? []) if (!vivi.has(id)) fatti.delete(id);\n  return fatti ?? new Set();'),
    ('HZ85', 'shared/volta/mods/arturo/azioni.js', 'for (const g of vista?.gruppi ?? []) for (const t of g.todo ?? []) vivi.add(t.id);', 'for (const g of (vista?.gruppi ?? []).slice(0, 1)) for (const t of g.todo ?? []) vivi.add(t.id);'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '  let scritto = Boolean(p) && p.nome === nome && Date.now() - p.quando < PORTA_MS;', '  let scritto = false;'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '  let scritto = Boolean(p) && p.nome === nome && Date.now() - p.quando < PORTA_MS;', '  let scritto = Boolean(p) && Date.now() - p.quando < PORTA_MS;'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '  let scritto = Boolean(p) && p.nome === nome && Date.now() - p.quando < PORTA_MS;', '  let scritto = Boolean(p) && p.nome === nome;'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '  let scritto = Boolean(p) && p.nome === nome && Date.now() - p.quando < PORTA_MS;', '  let scritto = Boolean(p) && p.nome === nome && Date.now() - p.quando <= PORTA_MS;'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '    if (scritto) portati.set(s.sessionId, { nome, quando: Date.now() });\n', ''),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '    if (scritto) portati.set(s.sessionId, { nome, quando: Date.now() });\n', '    portati.set(s.sessionId, { nome, quando: Date.now() });\n'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '    if (scritto) portati.set(s.sessionId, { nome, quando: Date.now() });\n', '    if (scritto) portati.set(s.sessionId, { nome, quando: 0 });\n'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', '  const p = portati.get(s.sessionId);', '  const p = [...portati.values()].pop();'),
    ('HZ85', 'shared/volta/mods/arturo/dati.js', 'export const PORTA_MS = 5 * 60 * 1000;', 'export const PORTA_MS = 5 * 1000;'),
    ('HZ82', 'shared/volta/installa-herdr.sh', '        if mia.get(k) in VECCHI:\n            del mia[k]\n', ''),
    ('HZ82', 'shared/volta/installa-herdr.sh', 'if mia.get(k) in VECCHI:', 'if k in mia:'),
    ('HZ82', 'shared/volta/installa-herdr.sh', 'if mia.get(k) in VECCHI:', 'if str(mia.get(k)).startswith("mod.open:arturo-"):'),
    ('HZ82', 'shared/volta/installa-herdr.sh', 'VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato")\n# Senza keys.json', 'VECCHI = ("mod.open:arturo-chrome", "mod.open:arturo-stato")\n# Senza keys.json'),
    ('HZ82', 'shared/volta/installa-herdr.sh', 'VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato")\n# Senza keys.json', 'VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-stato")\n# Senza keys.json'),
    ('HZ82', 'shared/volta/installa-herdr.sh', 'VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato")\n# Senza keys.json', 'VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome")\n# Senza keys.json'),
    ('HZ82', 'shared/volta/volta_mod.py', 'if mia.get(tasto) in TASTI_VECCHI or (', 'if False or ('),
    ('HZ82', 'shared/volta/volta_mod.py', 'if mia.get(tasto) in TASTI_VECCHI or (', 'if tasto in mia or ('),
    ('HZ82', 'shared/volta/volta_mod.py', 'if mia.get(tasto) in TASTI_VECCHI or (', 'if str(mia.get(tasto)).startswith("mod.open:arturo-") or ('),
    ('HZ82', 'shared/volta/volta_mod.py', 'TASTI_VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome", "mod.open:arturo-stato")', 'TASTI_VECCHI = ("mod.open:arturo-progetti", "mod.open:arturo-chrome")'),
    ('HZ82', 'shared/volta/volta_mod.py', '    try:\n        tasti(fonte)\n', '    try:\n        pass\n'),
    ('HZ82', 'shared/volta/volta_mod.py', '    if quanti:\n        scrivi(f, miei)', '    if False:\n        scrivi(f, miei)'),
    ('HZ81', 'shared/volta/mods/arturo/barra.js', '.size_full().overflow_hidden().bg(t.chrome)\n      .child(v_flex().id("barra-cima")', '.size_full().bg(t.chrome)\n      .child(v_flex().id("barra-cima")'),
    ('HZ81', 'shared/volta/mods/arturo/barra.js', 'setShared("arturo.misura.cima", v);', ''),
    ('HZ81', 'shared/volta/mods/arturo/volta.js', '.max_h(GESTI_MAX).flex_none().overflow_y_scroll()', ''),
    ('HZ81', 'shared/volta/layouts/arturo.json', '      "resizable": false,\n      "background": "chrome",', '      "background": "chrome",'),
    ('HZ81', 'shared/volta/layouts/arturo.json', '"px": 44', '"px": 48'),
    ('HZ104', 'shared/volta/mods/arturo/barra.js', 'const fila = [dove, tutto].filter(Boolean);', 'const fila = [dove].filter(Boolean);'),
    ('HZ105', 'shared/volta/mods/arturo/misure.js', 'export const MARGINE = SPAZIO.l;', 'export const MARGINE = 14;'),
    ('HZ105', 'shared/volta/mods/arturo/barra.js', '      .on_click(() => apriFinestra())\n      .accessibility_label("Cerca o chiedi")', '      .accessibility_label("Cerca o chiedi")'),
    ('HZ105', 'shared/volta/mods/arturo/barra.js', '          .child(campo)\n', '          .child(campo)\n          .child(pulsante("apri", "folder", "Apri un progetto", () => apriFinestra()))\n'),
    ('HZ105', 'shared/volta/mods/arturo/barra.js', '.id("barra-cima").flex_none().px(MARGINE)', '.id("barra-cima").flex_none().px(14)'),
    ('HZ105', 'shared/volta/mods/arturo/barra.js', '      .child(div().flex_1())\n', '      .child(voce("vuota"))\n'),
    ('HZ105', 'shared/volta/mods/arturo/barra.js', '{ misura: "piccolo", segnale: segnaleImpostazioni(Boolean(updates().app.ready)) }', '{ misura: "piccolo" }'),
    ('HZ105', 'shared/volta/mods/arturo/comuni.js', '    .tooltip(testo)\n    .accessibility_label(testo)\n', '    .tooltip(testo)\n'),
    ('HZ105', 'shared/volta/mods/arturo/comuni.js', 'if (rigaMod(shared("arturo.mod"))?.avviso) return "blocked";', 'if (false) return "blocked";'),
    ('HZ105', 'shared/volta/mods/arturo/comuni.js', 'h(PULSANTE[grande ? "grande" : "piccolo"])', 'h(36)'),
    ('HZ105', 'shared/volta/mods/arturo/volta.js', '.id(`vr-${s.host}-${s.id}`).relative().mx(MARGINE)', '.id(`vr-${s.host}-${s.id}`).relative().mx(8)'),
    ('HZ105', 'shared/volta/mods/arturo/volta.js', '.id(`vgh-${g.chiave || "senza"}`).mx(MARGINE)', '.id(`vgh-${g.chiave || "senza"}`).mx(8)'),
    ('HZ105', 'shared/volta/mods/arturo/volta.js', 'return h_flex().mx(MARGINE).mb(SPAZIO.s).h(PULSANTE.piccolo)', 'return h_flex().mx(14).mb(SPAZIO.s).h(PULSANTE.piccolo)'),
    ('HZ105', 'shared/volta/mods/arturo/volta.js', '.font_family(fontTerminale())', '.font_family("Atkinson Hyperlegible Mono")'),
    ('HZ105', 'shared/volta/mods/arturo/volta.js', 'o dalle tessere (${tasti().tessere}).`', 'o da Apri un progetto.`'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    return salvo if salvo in veri else (veri[0] if veri else None)', '    return salvo'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    return salvo if salvo in veri else (veri[0] if veri else None)', '    return veri[0] if veri else None'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', 'if x.get("uid") and VIRTUALE.lower() not in (x.get("nome") or "").lower()]', 'if x.get("uid")]'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    if not messo or a.predefinito() != messo:\n        return False\n    uid = vero(', '    if not messo:\n        return False\n    uid = vero('),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    prima = attuale if attuale != bh["uid"] else (vero(a) or "")', '    prima = attuale'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    return bool(uid) and a.metti(uid)', '    return bool(uid) and uid == stato.get("prima") and a.metti(uid)'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    return "volta_microfono" in riga and ruolo in riga.split()', '    return True'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    return "volta_microfono" in riga and ruolo in riga.split()', '    return "volta_microfono" in riga'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    return "volta_microfono" in riga and ruolo in riga.split()', '    return False'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    if nostro(stato.get("pid"), "ricevi"):\n        print(json.dumps({"esito": "ponte vivo"}))', '    if vivo(stato.get("pid")):\n        print(json.dumps({"esito": "ponte vivo"}))'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '    if nostro(stato.get("pid"), "ricevi"):\n        return esci(4,', '    if vivo(stato.get("pid")):\n        return esci(4,'),
    ('HZ78', 'shared/volta/mods/arturo/volta_microfono.py', '"ponte": nostro(r.get("pid"), "ricevi"),', '"ponte": vivo(r.get("pid")),'),
    ('HZ78', 'shared/volta/mods/arturo/volta_sonda.py', '        subprocess.run([sys.executable, mic, "ripara"], capture_output=True, stdin=subprocess.DEVNULL, timeout=10)', '        pass'),
    ('HZ78', 'shared/volta/mods/arturo/volta_sonda.py', 'if os.path.exists(os.path.join(vc, "microfono.json")) and os.path.exists(mic):', 'if os.path.exists(os.path.join(vc, "microfono-locale.json")) and os.path.exists(mic):'),
    ('HZ78', 'shared/volta/mods/arturo/volta_sonda.py', '        subprocess.run([sys.executable, mic, "ripara"], capture_output=True, stdin=subprocess.DEVNULL, timeout=10)', '        subprocess.run([sys.executable, mic, "stato"], capture_output=True, stdin=subprocess.DEVNULL, timeout=10)'),
    ('HZ79', 'shared/volta/mods/arturo/volta_microfono.py', '            if not scrivi_entro(uscita, pezzo, SILENZIO):\n                break', '            os.set_blocking(uscita, True)\n            os.write(uscita, pezzo)'),
    ('HZ79', 'shared/volta/mods/arturo/volta_microfono.py', '        resta = fine - time.time()\n        if resta <= 0:\n            return False', '        resta = 3600'),
    ('HZ79', 'shared/volta/mods/arturo/volta_microfono.py', '        suo = nostro(pid, "ponte") or (not vivo(pid) and gruppo_vivo(pid))', '        suo = nostro(pid, "ponte")'),
    ('HZ79', 'shared/volta/mods/arturo/volta_microfono.py', '        suo = nostro(pid, "ponte") or (not vivo(pid) and gruppo_vivo(pid))', '        suo = True'),
    ('HZ79', 'shared/volta/mods/arturo/volta_microfono.py', '                    os.killpg(pid, segnale)', '                    os.kill(pid, segnale)'),
    ('HZ79', 'shared/volta/mods/arturo/volta_microfono.py', '    if d.get("stato") in ("avvio", "attivo") and not nostro(d.get("pid"), "ponte"):', '    if d.get("stato") in ("avvio", "attivo") and not vivo(d.get("pid")):'),
    ('HZ79', 'shared/volta/mods/arturo/volta_microfono.py', '                if not gruppo_vivo(pid):\n                    break\n    file_locale().unlink(missing_ok=True)', '                if not gruppo_vivo(pid):\n                    break\n        return\n    file_locale().unlink(missing_ok=True)'),
    ('HZ80', 'shared/volta/mods/arturo/volta_microfono.py', '    if "permission denied (publickey" in t or "host key verification failed" in t:\n        return "l\'altra macchina non accetta la chiave ssh di questa"\n', ''),
    ('HZ80', 'shared/volta/mods/arturo/volta_microfono.py', '    if "permission denied (publickey" in t or "host key verification failed" in t:', '    if "host key verification failed" in t:'),
    ('HZ80', 'shared/volta/mods/arturo/volta_microfono.py', '    if "permission denied (publickey" in t or "host key verification failed" in t:', '    if "permission denied (publickey" in t:'),
    ('HZ80', 'shared/volta/mods/arturo/microfono.js', '  if (/\\.exe$/i.test(String(a[3])) || /^[a-z]:[\\\\/]/i.test(String(a[3]))) return null;\n', ''),
    ('HZ80', 'shared/volta/mods/arturo/microfono.js', '/\\.exe$/i.test(String(a[3])) || ', ''),
    ('HZ80', 'shared/volta/mods/arturo/microfono.js', ' || /^[a-z]:[\\\\/]/i.test(String(a[3]))', ''),
    ('HZ80', 'shared/volta/mods/arturo/microfono.js', '/\\.exe$/i.test(String(a[3]))', '/\\.exe$/.test(String(a[3]))'),
    ('HZ80', 'shared/volta/mods/arturo/microfono.js', '/^[a-z]:[\\\\/]/i.test(String(a[3]))', '/^[a-z]:\\\\/i.test(String(a[3]))'),
    ('HZ80', 'shared/volta/mods/arturo/microfono.js', '/\\.exe$/i.test(String(a[3]))', '/exe/i.test(String(a[3]))'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '  if (!s?.id || schedeDi(s).length) return [];\n  return terminals().filter(', '  if (!s?.id) return [];\n  return terminals().filter('),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', 'return terminals().filter((x) => !String(x.address).includes("/") && (x.state ?? "live") === "live" &&', 'return terminals().filter((x) => (x.state ?? "live") === "live" &&'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '!String(x.address).includes("/") && (x.state ?? "live") === "live" &&', '!String(x.address).includes("/") &&'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '(x.state ?? "live") === "live" &&', 'x.state === "live" &&'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '!occupataDaAltra(x, s) && suaScheda(x, s, ambiguo(s.id)));', '!occupataDaAltra(x, s) && agganciata(x.argv, s));'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '!occupataDaAltra(x, s) && suaScheda(x, s, ambiguo(s.id)));', '!occupataDaAltra(x, s) && etichettaDice(x.labels?.[ETICHETTA], s, ambiguo(s.id)) === true);'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '  for (const t of l) { segnaTolto(t.address); run("terminal.kill", { terminal: t.address }); }\n  return l.length;', '  return l.length;'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '  for (const t of l) { segnaTolto(t.address); run("terminal.kill", { terminal: t.address }); }\n  return l.length;', '  for (const t of l.slice(0, 1)) { segnaTolto(t.address); run("terminal.kill", { terminal: t.address }); }\n  return l.length;'),
    ('HZ77', 'shared/volta/mods/arturo/dati.js', '  for (const t of l) { segnaTolto(t.address); run("terminal.kill", { terminal: t.address }); }\n  return l.length;', '  for (const t of l) { segnaTolto(t.address); run("terminal.kill", { terminal: t.address }); }\n  return 0;'),
    ('HZ77', 'shared/volta/mods/arturo/volta.js', '    if (d.azione === "aggancia" && this.fuori(s, secondo, cx)) return;\n', ''),
    ('HZ77', 'shared/volta/mods/arturo/volta.js', '    const secondo = this.avvisi[chiave(s)] === ALTROVE;\n    delete this.avvisi[chiave(s)];', '    delete this.avvisi[chiave(s)];\n    const secondo = this.avvisi[chiave(s)] === ALTROVE;'),
    ('HZ77', 'shared/volta/mods/arturo/volta.js', '    if (secondo) { stacca(s); return false; }\n', ''),
    ('HZ77', 'shared/volta/mods/arturo/volta.js', '    if (!altrove(s).length) return false;\n', ''),
    ('HZ77', 'shared/volta/mods/arturo/volta.js', '    this.avvisa(s, ALTROVE, cx, ALTROVE_MS);\n    return true;', '    this.avvisa(s, ALTROVE, cx, ALTROVE_MS);\n    return false;'),
    ('HZ74', 'shared/volta/mods/arturo/volta_sonda.py', '        if nuovo.get("progetto"):\n            s["progetto"] = nuovo["progetto"].strip()[:60]', '        if False:\n            s["progetto"] = nuovo["progetto"].strip()[:60]'),
    ('HZ74', 'shared/volta/mods/arturo/volta_sonda.py', '        nuovo.update(progetto=s["progetto"], fonte=fonte)', '        pass'),
    ('HZ74', 'shared/volta/mods/arturo/volta_sonda.py', 'FORTI = ("persona", "inizio", "volta", "teletrasporto", "file")', 'FORTI = ("persona", "inizio", "volta", "teletrasporto", "file", "cartella")'),
    ('HZ74', 'shared/volta/mods/arturo/volta_sonda.py', 'FORTI = ("persona", "inizio", "volta", "teletrasporto", "file")', 'FORTI = ("persona", "inizio", "volta", "teletrasporto", "file", "prompt")'),
    ('HZ74', 'shared/volta/mods/arturo/volta_sonda.py', '    k = s.get("id") if s.get("kind") == "background" else', '    k = s.get("sessionId", "")[:8] if s.get("kind") == "background" else'),
    ('HZ74', 'shared/volta/mods/arturo/volta_sonda.py', '    elif fonte in (None, "", "cartella"):', '    elif fonte == "cartella":'),
    ('HZ74', 'shared/volta/mods/arturo/volta_sonda.py', '        if nuovo != {x: v for x, v in reg.items() if x != "quando"} and (len(nuovo) > 1 or reg):\n', '        if False:\n'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', '        elif s["progetto"] and s["progetto"].lower() in basi:', '        elif False:'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', 'for x in (base, casa)}', 'for x in (base,)}'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', 's["progetto"].lower() in basi:', 's["progetto"] in basi:'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', '        base = json.load(fh).get("base")\n', '        base = None\n'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', '("pid-%d" % s["pid"] if isinstance(s.get("pid"), int) else None)', 'None'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', '(n.startswith("pid-") or time.time()', '(False or time.time()'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', 'os.path.getmtime(f) > LAVORI_GIORNI * 86400):', 'os.path.getmtime(f) > LAVORI_GIORNI * 86400000):'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', 'n[:-5] not in vivi and (', '('),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', 'vivi = {lavoro_di(s) for s in tutte}', 'vivi = {lavoro_di(s) for s in sessioni}'),
    ('HZ75', 'shared/volta/mods/arturo/volta_sonda.py', 'and (len(nuovo) > 1 or reg):', 'and True:'),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '    scrivi(os.path.join(cache, "volta-lavori", corto + ".json"),\n           {"progetto": a["progetto"], "fonte": "volta", "sessionId": sid, "quando": time.time()})', '    pass'),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '    if scritto:\n        nuovo["titolo"] = s["titolo"]', '    if False:\n        nuovo["titolo"] = s["titolo"]'),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '    elif nuovo.get("titolo") and reg.get("sessionId") != sid:', '    elif False:'),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '    elif nuovo.get("titolo") and reg.get("sessionId") != sid:', '    elif nuovo.get("titolo"):'),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '"quando": time.time(), "peso": 0, "portato": True})', '"quando": time.time(), "peso": 0, "portato": False})'),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '        scrivi(ftit, {"titolo": s["titolo"], "fonte": "persona", "quando": time.time(), "peso": 0, "portato": True})\n', ''),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '            scritto = tit.get("fonte") == "persona"', '            scritto = True'),
    ('HZ76', 'shared/volta/mods/arturo/volta_sonda.py', '        nuovo.pop("titolo", None)', '        pass'),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", "ATTESA_LETTURA = 45", "ATTESA_LETTURA = 55"),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", "        return lancia(argv(t), timeout=t + margine)", "        return lancia(argv(t), timeout=90)"),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", "    return int(entro - time.monotonic()) if entro is not None else", "    return 30 if entro is not None else"),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", 'lambda t: hc() + ["exec", "--on", nome, "--timeout", str(t), py, "-c",', 'lambda t: hc() + ["exec", "--on", nome, py, "-c",'),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", "% (max(2, t - 3), compressa)],", "% (40, compressa)],"),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", "timeout=max(2, min(40, scade - time.time())))", "timeout=40)"),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", '        raise RuntimeError("non ha risposto in %d s" % t) from None', "        raise"),
    ("HZ69", "shared/volta/mods/arturo/volta_sonda.py", '        guasto[0] = "claude agents non ha risposto in tempo"\n        return None', "        return []"),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", 'voci = json.loads(out).get("machines", []) if rc == 0 else None', 'voci = json.loads(out).get("machines", []) if rc == 0 else []'),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", "    except (ValueError, AttributeError):\n        voci = None\n    if not isinstance(voci, list):\n        return None", "    except (ValueError, AttributeError):\n        voci = []\n    if not isinstance(voci, list):\n        return None"),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", "    if not isinstance(voci, list):\n        return None", "    if not isinstance(voci, list):\n        return []"),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", "    except FileNotFoundError:\n        return []\n    except (OSError, subprocess.SubprocessError):\n        return None", "    except FileNotFoundError:\n        return []\n    except (OSError, subprocess.SubprocessError):\n        return []"),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", "    except FileNotFoundError:\n        return []\n", "    except FileNotFoundError:\n        return None\n"),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", "                 for m in (prima or []) if isinstance(m, dict)", "                 for m in [] if isinstance(m, dict)"),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", '        if "irraggiungibile" in v:\n            return v\n        if not v["questa"]', '        if not v["questa"]'),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", '        if note is None:\n            return {"errore": "Herdr non dice le macchine: riprova fra poco"}\n', "        note = note or []\n"),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", '"~/.local/bin/hc" + (".exe" if os.name == "nt" else "")', '"~/.local/bin/hc"'),
    ("HZ70", "shared/volta/mods/arturo/volta_sonda.py", '(precedente or {}).get("macchine"), entro), precedente)', "None, entro), precedente)"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", "    v = elenco(r.stdout)\n    if v is None:", "    try:\n        v = json.loads(r.stdout)\n    except ValueError:\n        v = None\n    if v is None:"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", '    print(json.dumps({"errore": guasto[0] or "claude agents non risponde"})); raise SystemExit', "    sessioni = []"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", '        guasto[0] = "claude agents: " + (righe[0][:140] if righe else "uscita %d" % r.returncode)\n        return None', "        return []"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", '    if v is None:\n        guasto[0] = "claude agents: risposta senza elenco"\n    return v', "    return v or []"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", "        i = testo.find(\"[\", i + 1)\n    return None\n'''", "        break\n    return None\n'''"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", "        if isinstance(v, list) and all(isinstance(x, dict) for x in v):\n            return v", "        if isinstance(v, list):\n            return v"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", '        for s in elenco(r.stdout) or []:\n            if s.get("id") == corto', '        for s in json.loads(r.stdout or "[]"):\n            if s.get("id") == corto'),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", "for giro in range(3):", "for giro in range(1):"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", '    sessioni = elenco(out) if (out or "").strip() else []', '    sessioni = json.loads(out[out.find("["):])'),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", '    if d.get("errore"):\n        raise RuntimeError(str(d["errore"])[:200])\n    return d', "    return d"),
    ("HZ71", "shared/volta/mods/arturo/volta_sonda.py", 'NASCI = NASCI.replace("#ELENCO#", ELENCO.strip()).replace("#CLAUDE#", CERCA_CLAUDE.strip())\n', ""),
    ("HZ72", "shared/volta/mods/arturo/volta_sonda.py", "        if not isinstance(d, dict):  # una riga tagliata a metà può essere un numero o una stringa\n            continue\n", ""),
    ("HZ72", "shared/volta/mods/arturo/volta_sonda.py", "        if not isinstance(m, dict):\n            continue\n", ""),
    ("HZ73", "shared/volta/mods/arturo/dati.js", ' && (r?.code === 0 || d.errore)) return d;', ') return d;'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", '.filter((x) => x.startsWith("{"));\n  let d = null;', '.filter(Boolean);\n  let d = null;'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", '/^Traceback/.test(caduto[0] ?? "") ? caduto[caduto.length - 1] : prima(r?.stderr) || detto;', 'prima(r?.stderr) || detto;'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", 'prima(r?.stderr) || detto;', 'detto || prima(r?.stderr);'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", 'const detto = d ? "" : prima(r?.stdout);', 'const detto = prima(r?.stdout);'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", '(r?.code ? `uscita ${r.code}` : "nessuna risposta")).slice(0, 200) };', '(r?.code ? `uscita ${r.code}` : "nessuna risposta")) };'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", '(motivo || (r?.code ? `uscita ${r.code}` : "nessuna risposta"))', '(motivo || "nessuna risposta")'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", "{ timeout: riavvia ? 210000 : 150000 });\n    return esito(r);", '{ timeout: riavvia ? 210000 : 150000 });\n    return JSON.parse((r.stdout || "").trim() || "{}");'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", '...(valore ? ["--", valore] : [])], { timeout: 90000 });\n    return esito(r);', '...(valore ? ["--", valore] : [])], { timeout: 90000 });\n    return JSON.parse((r.stdout || "").trim() || "{}");'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", '{ timeout: verbo === "respawn" ? 210000 : 90000 });\n    return esito(r);', '{ timeout: verbo === "respawn" ? 210000 : 90000 });\n    return JSON.parse((r.stdout || "").trim() || "{}");'),
    ("HZ73", "shared/volta/mods/arturo/dati.js", "      nata = esito(await exec(c.arturo[0], args, { timeout: 360000 }));", '      nata = JSON.parse(((await exec(c.arturo[0], args, { timeout: 360000 })).stdout || "").trim() || "{}");'),
    ("HZ73", "shared/volta/mods/arturo/volta.js", 'portata = esito(await exec(this.py, [this.sposta, "porta-volta", s.host, s.sessionId], { timeout: 60000 }));', 'portata = JSON.parse((await exec(this.py, [this.sposta, "porta-volta", s.host, s.sessionId], { timeout: 60000 })).stdout || "{}");'),
    ("HZ66", "shared/volta/mods/arturo/dati.js", "  return ora - n.da < NASCITA_MAX ? n.macchina : null;", "  return n.macchina;"),
    ("HZ66", "shared/volta/mods/arturo/dati.js", "const NASCITA_MAX = 420000;", "const NASCITA_MAX = 360000;"),
    ("HZ66", "shared/volta/mods/arturo/dati.js", '  if (!n || typeof n !== "object" || typeof n.macchina !== "string" || !Number.isFinite(n.da)) return null;',
     '  if (!n) return null;\n  if (typeof n === "string") return n;'),
    ("HZ66", "shared/volta/mods/arturo/dati.js", ' || !Number.isFinite(n.da)) return null;', ') return null;\n  if (!Number.isFinite(n.da)) return n.macchina;'),
    ("HZ66", "shared/volta/mods/arturo/dati.js", '  if (inNascita()) return dico("Sta già nascendo', '  if (false) return dico("Sta già nascendo'),
    ("HZ66", "shared/volta/mods/arturo/dati.js", '    if (!copia) notify({ title: titolo, body: errore, level });\n', ""),
    ("HZ66", "shared/volta/mods/arturo/dati.js", '    if (shared("arturo.nascita")?.da === da) setShared("arturo.nascita", null);\n', ""),
    ("HZ66", "shared/volta/mods/arturo/dati.js", '  setShared("arturo.nascita", { macchina, da });', '  setShared("arturo.nascita", macchina);'),
    ("HZ66", "shared/volta/mods/arturo/dati.js", 'return v.errore ? dico("La sessione è nata, ma non si apre", v.errore) : { ok: true, id: nata.id };',
     'return v.errore ? { errore: v.errore } : { ok: true, id: nata.id };'),
    ("HZ66", "shared/volta/mods/arturo/comuni.js", "const nascita = inNascita();", 'const nascita = shared("arturo.nascita");'),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", '  if (c === "volta-nuova") return { verbo: "volta-nuova", arg: null, lungo: true };\n', ""),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", '  if (c.startsWith("volta-menu-")) return { verbo: "volta-menu", arg: dopo("volta-menu-"), lungo: false };\n', ""),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", '  if (c.startsWith("volta-cambia-")) return { verbo: "volta-cambia", arg: c, lungo: false };\n', ""),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", '  if (g) return { verbo: "volta-gesto", arg: { verbo: g[1], id: g[2] }, lungo: false };\n', ""),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", 'if (c === "nuova") return { verbo: "nuova", arg: null, lungo: true };', 'if (c === "nuova") return { verbo: "nuova", arg: null, lungo: false };'),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", 'return { verbo: "progetto", arg: dopo("apri-"), lungo: true };', 'return { verbo: "progetto", arg: dopo("apri-"), lungo: false };'),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", 'if (c === "apri") return { verbo: "apri", arg: null, lungo: false };\n', ""),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", "export const comandoApri = (slug) => `arturo.apri-${slug}`;", "export const comandoApri = (slug) => `arturo.apri.${slug}`;"),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", "Math.max(0, Number(dopo(\"guida\") || 1) - 1)", "Number(dopo(\"guida\") || 1)"),
    ("HZ67", "shared/volta/mods/arturo/apri.js", '    else if (r.tipo === "progetto") run(comandoApri(slug(r.nome)));', '    else if (r.tipo === "progetto") { apri(r.nome).finally(() => this.chiudi()); return; }'),
    ("HZ67", "shared/volta/mods/arturo/revisione.js", ".on_click(() => { run(comandoApri(k)); this.chiudi(); })", ".on_click(async () => { try { await apri(k); } finally { this.chiudi(); } })"),
    ("HZ67", "shared/volta/mods/arturo/suggerimenti.js", '.on_click(() => { if (sug.dove === "apri") apriFinestra(); else run(comandoSuggerimento(sug.id)); dopo?.(); })',
     ".on_click(async () => { try { await esegui(sug); } finally { dopo?.(); } })"),
    ("HZ67", "shared/volta/mods/arturo/testata.js", '() => run("arturo.nuova"),', "() => nuova(),"),
    ("HZ67", "shared/volta/mods/arturo/barra.js", "        try { this.comando(instrada(c), cx); } catch (e) { this.rotto(c, e); }\n", "        this.comando(instrada(c), cx);\n"),
    ("HZ67", "shared/volta/mods/arturo/barra.js", "      try { await lavoro(); } catch (e) { this.rotto(c, e); }\n", "      await lavoro();\n"),
    ("HZ67", "shared/volta/mods/arturo/barra.js", "        try { this.comando(instrada(c), cx); } catch (e) { this.rotto(c, e); }\n",
     "        try { await this.comando(instrada(c), cx); } catch (e) { this.rotto(c, e); }\n"),
    ("HZ67", "shared/volta/mods/arturo/barra.js", 'else if (c === "nuova") this.lungo(c, cx, () => (arg ? nuova(decodifica(arg)) : nuova()));', 'else if (c === "nuova") return nuova();'),
    ("HZ68", "shared/volta/mods/arturo/comandi.js", "Boolean(nascosta) && c !== PING && instrada(c).verbo !== null;", "Boolean(nascosta) && instrada(c).verbo !== null;"),
    ("HZ68", "shared/volta/mods/arturo/comandi.js", "Boolean(nascosta) && c !== PING && instrada(c).verbo !== null;", "c !== PING && instrada(c).verbo !== null;"),
    ("HZ68", "shared/volta/mods/arturo/comandi.js", "Boolean(nascosta) && c !== PING && instrada(c).verbo !== null;", "Boolean(nascosta) && c !== PING;"),
    ("HZ68", "shared/volta/mods/arturo/testata.js", '    if (!daRimandare(c, Boolean(trova(layout(), "sidebar")?.hidden))) return;\n', ""),
    ("HZ68", "shared/volta/mods/arturo/testata.js", '    run("layout.toggle", { id: "sidebar" });\n', ""),
    ("HZ68", "shared/volta/mods/arturo/testata.js", '      if (Number(shared("arturo.barra.viva")) >= da) return run(`arturo.${c}`);\n', ""),
    ("HZ68", "shared/volta/mods/arturo/testata.js", "        try { await this.rimanda(c, cx); } catch {", "        try { } catch {"),
    ("HZ68", "shared/volta/mods/arturo/barra.js", '    if (c === "ci-sei") setShared("arturo.barra.viva", Date.now());\n    else if (c === "apri")', '    if (c === "apri")'),
    ("HZ65", "shared/volta/mods/arturo/dati.js", "      if (await tornataShell(g)) return;\n", ""),
    ("HZ65", "shared/volta/mods/arturo/dati.js", "  if (!a && (await tornataShell(g))) return;\n", ""),
    ("HZ65", "shared/volta/mods/arturo/dati.js", "  if (!(await nuda(g.terminal))) return false;\n  const s = await sessioneDi(g);", "  if (true) return false;\n  const s = await sessioneDi(g);"),
    ("HZ65", "shared/volta/mods/arturo/dati.js", "filter((x) => x?.id === g.id && Array.isArray(x.attach));", "filter((x) => Array.isArray(x.attach));"),
    ("HZ65", "shared/volta/mods/arturo/dati.js", "  if (!a && (await tornataShell(g))) return;\n", "  if (await tornataShell(g ?? { terminal: a.address, id: \"ffff1111\" })) return;\n"),
    ("HZ65", "shared/volta/mods/arturo/dati.js", "    notify({ title: \"Ho riaperto la sessione\", body: \"Riprova fra qualche secondo.\", level: \"warning\" });\n", ""),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "            figlio.kill()\n        rimetti(a, stato)\n", "            figlio.kill()\n"),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "    if nostro(stato.get(\"pid\"), \"ricevi\"):\n        return esci(4,", "    if False:\n        return esci(4,"),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "    if not bh:\n        return esci(3, esito=\"errore\", motivo=\"manca BlackHole\")\n", "    bh = bh or a.ingressi()[0]\n"),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "    if not messo or a.predefinito() != messo:\n        return False\n    uid = vero(", "    if not messo:\n        return False\n    uid = vero("),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "            if not pronto:\n                break\n", "            if not pronto:\n                continue\n"),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "                    if time.time() - file_rinnovo().stat().st_mtime > SCADENZA:", "                    if time.time() - file_rinnovo().stat().st_mtime > SCADENZA * 1000:"),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "    if stesso and d.get(\"stato\") in (\"avvio\", \"attivo\") and nostro(d.get(\"pid\"), \"ponte\"):\n        print(json.dumps(stato_locale(), ensure_ascii=False))\n        return 0\n", ""),
    ("HZ63", "shared/volta/mods/arturo/volta_microfono.py", "                elif d.get(\"esito\") == \"errore\":\n                    fermo[\"motivo\"] = d.get(\"motivo\") or \"errore sull'altra macchina\"\n", ""),
    ("HZ63", "shared/volta/mods/arturo/microfono.js", " || a[4] !== \"attach\") return null;", ") return null;"),
    ("HZ63", "shared/volta/mods/arturo/microfono.js", "x.id === id && !x.questa && Array.isArray(x.attach)", "x.id === id && Array.isArray(x.attach)"),
    ("HZ63", "shared/volta/mods/arturo/microfono.js", "if (!target || target.startsWith(\"-\")) return null;", "if (!target) return null;"),
    ("HZ63", "shared/volta/mods/arturo/microfono.js", "  if (adesso - st.visto > TENUTA) return { st: null, azione: { verbo: \"spegni\" } };", "  if (adesso - st.visto > TENUTA * 1000) return { st: null, azione: { verbo: \"spegni\" } };"),
    ("HZ63", "shared/volta/mods/arturo/microfono.js", "    if (!acceso || st.target !== b.target)", "    if (!acceso)"),
    ("HZ63", "shared/volta/mods/arturo/volta.js", "    cx.timer.every(OGNI_MICROFONO, (cx) => this.microfono(cx));\n", ""),
    ("HZ61", "shared/volta/mods/arturo/barra.js", "      if (!this.memoria) {\n", "      {\n"),
    ("HZ61", "shared/volta/mods/arturo/dati.js", "    const k = capo.get(chiave(p)) ?? chiave(p);", "    const k = chiave(p);"),
    ("HZ61", "shared/volta/mods/arturo/dati.js", "  for (const nome of memoria ? [] : extra.cartelle ?? []) {", "  for (const nome of extra.cartelle ?? []) {"),
    ("HZ61", "shared/volta/mods/arturo/dati.js", 'ferma: noto && Boolean(limite) && (m.data || "") < limite });', "ferma: false });"),
    ("HZ61", "shared/volta/mods/arturo/dati.js", '(noto || !conCategorie ? "" : "Altre cartelle")', '""'),
    ("HZ61", "shared/volta/mods/arturo/dati.js", "  return r.ok && Array.isArray(r.json?.progetti) ? r.json.progetti : null;", "  return r.json?.progetti ?? [];"),
    ("HZ61", "shared/volta/mods/arturo/dati.js", "  return m ? m.map((p) => (p.cartella ? p.nome : p.slug)).filter(Boolean) : cartelle();", "  return cartelle();"),
    ("HZ61", "shared/volta/mods/arturo/apri.js", "await Promise.all([nomiProgetti(), sessioniVolta()]);", "await Promise.all([cartelle(), sessioniVolta()]);"),
    ("HZ62", "shared/volta/mods/arturo/nota.js", "Math.min(q.x, W - larga - 4 - (dentro ? 4 : 0))", "q.x"),
    ("HZ62", "shared/volta/mods/arturo/nota.js", "const sotto = !sopra && q.altezza < 60 &&", "const sotto = false &&"),
    ("HZ62", "shared/volta/mods/arturo/nota.js", ".sort((a, b) => a.width * a.height - b.width * b.height ||", ".sort((a, b) => b.width * b.height - a.width * a.height ||"),
    ("HZ62", "shared/volta/mods/arturo/nota.js", 'typeof e.id === "string" && !e.own && ', 'typeof e.id === "string" && '),
    ("HZ62", "shared/volta/mods/arturo/nota.js", "  if (Object.hasOwn(NOMI_ELEMENTO, k)) return NOMI_ELEMENTO[k];\n", ""),
    ("HZ62", "shared/volta/mods/arturo/nota.js", "const radice = e.id.startsWith(RADICE) ? e : validi.find((x) => x.view === e.view && x.id.startsWith(RADICE));", "const radice = e.id.startsWith(RADICE) ? e : validi.find((x) => x.id.startsWith(RADICE));"),
    ("HZ62", "shared/volta/mods/arturo/nota.js", "  if (!el && !r?.rettangolo) return null;\n  const q = el ? el.rettangolo : r.rettangolo,", "  if (!r?.rettangolo) return null;\n  const q = r.rettangolo,"),
    ("HZ64", "shared/volta/mods/arturo/notaui.js", 'const ELEMENTI = typeof W?.elements === "function" && typeof W?.track_elements === "function";', "const ELEMENTI = true;"),
    ("HZ64", "shared/volta/mods/arturo/notaui.js", "  close() { segui(false); }", "  close() {}"),
    ("HZ64", "shared/volta/mods/arturo/testata.js", 'div().id("stato-tasti").text_color', "div().text_color"),
    ("HZ32", "bin/note_finestra.py", '"parte": None, "elemento": None,', '"parte": None,'),
    ("HZ60", "shared/volta/mods/arturo/volta_sonda.py", 'SONDA = SONDA.replace("#TERMINALE#", TERMINALE.strip())\n', ''),
    ("HZ60", "shared/volta/mods/arturo/volta_sonda.py", '        s["terminale"] = terminale_di(s["pid"])', '        s["terminale"] = None'),
    ("HZ60", "shared/volta/mods/arturo/volta_sonda.py", "base64.b64encode(zlib.compress(senza_commenti(SONDA).encode(), 9)).decode()", "base64.b64encode(senza_commenti(SONDA).encode()).decode()"),
    ("HZ60", "shared/volta/mods/arturo/volta_sonda.py", "    if os.name != \"nt\":\n        try:\n            amb = subprocess.run([\"ps\"", "    if os.name == \"nt\":\n        try:\n            amb = subprocess.run([\"ps\""),
    ("HZ60", "shared/volta/mods/arturo/volta_sonda.py", '                if riga.startswith("HC_TERMINAL_ID="):', '                if riga.startswith("HC_TERMINALE="):', "windows"),
    ("HZ60", "shared/volta/mods/arturo/volta_sonda.py", "            blocco = numero(parametri + 0x80) if parametri else 0", "            blocco = numero(parametri + 0x70) if parametri else 0", "windows"),
    ("HZ56", "shared/volta/keys.json", '"cmd-o": "arturo.apri",', '"cmd-o":  "arturo.apri",'),
    ("HZ57", "shared/volta/mods/arturo/volta.js", "  if (controlloMod || !(await esiste(script))) return;", "  if (!(await esiste(script))) return;"),
    ("HZ57", "shared/volta/mods/arturo/volta.js", "    cx.timer.every(OGNI_MOD, () => controllaMod(this.py));", ""),
    ("HZ57", "shared/volta/mods/arturo/sessioni.js", "adesso / 1000 - m.giu_da > 86400", "adesso / 1000 - m.giu_da > 0"),
    ("HZ57", "shared/volta/mods/arturo/sessioni.js", "d.toDateString() === oggi.toDateString() ? \"\" :", "true ? \"\" :"),
    ("HZ57", "shared/volta/mods/arturo/comuni.js", '.when(Boolean(rigaMod(shared("arturo.mod"))), (el) =>', '.when(false, (el) =>'),
    ("HZ57", "shared/volta/mods/arturo/barra.js", '`Impostazioni · ${rigaMod(shared("arturo.mod"))?.testo ?? tasti().impostazioni}`', '"Impostazioni"'),
    ("HZ57", "shared/volta/mods/arturo/sessioni.js", 'if (plugin?.esito === "compromesso")', 'if (false)'),
    ("HZ35", "shared/volta/volta-claude.sh", 'if [ -z "${SSH_CONNECTION:-}" ] && [ -f "$sonda" ]', 'if [ -f "$sonda" ]'),
    ("HZ35", "shared/volta/volta-claude.sh", '  esito=$(python3 "$sonda" servizio qui 2>&1) ||', '  esito=$(true) ||'),
    ("HZ35", "shared/volta/volta-claude.sh", 'servizio qui 2>&1) ||', 'servizio qui 2>&1) || exit 1 ||'),
    ("HZ38", "shared/volta/volta-claude.ps1", "if (-not $env:SSH_CONNECTION -and $py", "if ($py"),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '    if verbo == "respawn":\n        s = servizio(nome)', '    if False:\n        s = servizio(nome)'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '            return {"errore": "il servizio di Claude non parte su %s: %s" % (chi(nome), s["errore"])}\n    try:', '            pass\n    try:'),
    ("HZ42", "shared/volta/mods/arturo/dati.js", 'verbo === "respawn" ? 210000 : 90000', 'verbo === "respawn" ? 150000 : 90000'),
    ("HZ43", "shared/volta/mods/arturo/volta_sonda.py", 'etichetta = "org.stellakamikaze.arturo.claude-daemon"', 'etichetta = "org.stellakamikaze.arturo.claude"'),
    ("HZ43", "shared/volta/installa-herdr.sh", "schtasks /query /tn ArturoServizioClaude ", "schtasks /query /tn ArturoServizio "),
    ("HZ43", "shared/setup-herdr.md", "`HERDR SERVIZIO`", "la riga del servizio"),
    ("HZ42", "shared/volta/mods/arturo/dati.js", "{ timeout: 360000 }", "{ timeout: 200000 }"),
    ("HZ42", "shared/volta/mods/arturo/volta_sonda.py", "            t = min(90, int(entro - time.monotonic()))", "            t = 90"),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", "if acceso():\n    esci(acceso=True, come=\"già acceso\")", "if False:\n    pass"),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", "(#5208)\n    s = servizio(nome)\n", "(#5208)\n    s = {}\n"),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '"--name", "servizio-claude", "--no-parent", "--rm",', '"--name", "servizio-claude", "--rm",'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", 'subprocess.Popen([cl, "daemon", "run"], cwd=casa, start_new_session=True, **nulla)\n        come = "staccato"\nelif', 'subprocess.Popen([cl, "daemon", "run"], cwd=casa, **nulla)\n        come = "staccato"\nelif'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '        return {"errore": d.get("errore") or "acceso con hc run, ma non risponde ancora"}', '        return {"come": "terminale di Herdr"}'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '"--bg", claude_per_hc_run(d), "daemon", "run"],', '"--bg", "claude", "daemon", "run"],'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '        esci(serve="hc-run", claude=cl)\n    else:\n        subprocess.Popen([cl, "daemon", "run"], cwd=casa, start_new_session=True', '        esci(serve="hc-run")\n    else:\n        subprocess.Popen([cl, "daemon", "run"], cwd=casa, start_new_session=True'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '            and re.search(r"[\\\\/]claude(\\.exe)?$", cl) and', '            and'),
    ("HZ01", "shared/volta/installa-herdr.sh", '"frame.welcomed": "skipped"', '"frame.welcomed": "finished"'),
    ("HZ02", "shared/volta/installa-herdr.sh", "if k in mia and mia[k] != v and mia[k] not in PRENDE.get(v, ()):", "if False:"),
    ("HZ03", "shared/volta/installa-herdr.sh", 'Arturo funziona lo stesso nel Terminale."; exit 0 ;;', 'Arturo funziona lo stesso nel Terminale." ;;'),
    ("HZ04", "hooks/herdr-stato.sh", '[ -n "${HC_TERMINAL_ID:-}" ] || exit 0', ":"),
    ("HZ05", "settings.json", "herdr-stato.sh done", "herdr-stato.sh idle"),
    ("HZ09", "shared/volta/mods/arturo/dati.js", 'prompt: "/guidami"', 'prompt: "/guidamii"'),
    ("HZ10", "shared/volta/mods/arturo/partenza.js", "catena.slice(qui + 1)", "catena.slice(qui)"),
    ("HZ11", "shared/volta/mods/arturo/settimana.js", "else if (te) liste.te.push", "if (te) liste.te.push"),
    ("HZ12", "shared/volta/mods/arturo/azioni.js", "if (quando === t.quando) continue;", ""),
    ("HZ12", "shared/volta/mods/arturo/azioni.js", 'argv: ["inizia"', 'argv: ["riprendi"'),
    ("HZ12", "shared/volta/mods/arturo/todo.js", "const g = inizia(item);", "const g = null;"),
    ("HZ14", "shared/volta/mods/arturo/nota.js", "if (!t) return null;", ""),
    ("HZ14", "shared/volta/mods/arturo/nota.js", '"--chi", "io"', '"--chi", "tu"'),
    ("HZ13", "shared/volta/arturo-app.sh", 'python3 - "$plist" "$copia/arturo-app.sh"', 'python3 - "$plist" "$qui/arturo-app.sh"'),
    ("HZ13", "shared/volta/arturo-app.sh", '-c "Set :CFBundleIdentifier $ID"', '-c "Set :CFBundleIdentifier dev.herdr.app"'),
    ("HZ13", "shared/volta/arturo-app.sh", 'if [ -d "$arturo" ] && { [ ! -d "$herdr" ] || ! piu_nuova "$v_herdr" "$v_arturo"; }; then base=$arturo; fi', ":"),
    ("HZ06", "shared/volta/installa-herdr.sh", '[ "$firma" = assente ]', '[ "$firma" = mai ]'),
    ("HZ07", "shared/volta/mods/arturo/main.js", 'from "./notaui.js"', 'from "./notaui-perso.js"'),
    ("HZ07", "shared/volta/mods/arturo/main.js", ", nota: Nota, note: Note, casa: Casa,", ", note: Note, casa: Casa,"),
    ("HZ07", "shared/volta/layouts/arturo.json", '"parte": "stato"', '"parte": "stato-perso"'),
    ("HZ16", "shared/volta/servizi-gui.sh", "plist herdr-core false", "plist herdr-core true"),
    ("HZ16", "shared/volta/servizi-gui.sh", 'rm -f "$agenti/$PREFISSO.claude-daemon.plist"', 'plist claude-daemon true "$claude" daemon run'),
    ("HZ15", ".gitignore", "data/note-finestra/\n", ""),
    ("HZ15", ".gitignore", "data/herdr-invito\n", ""),
    ("HZ17", "shared/volta/mods/arturo/sessioni.js", "|| titolo(a).localeCompare(titolo(b)));", "|| titolo(b).localeCompare(titolo(a)));"),
    ("HZ17", "shared/volta/mods/arturo/sessioni.js", "if (note.length && out.length) out[out.length - 1].nota", "if (note.length && out.length) out[0].nota"),
    ("HZ18", "shared/volta/mods/arturo/sessioni.js", 'if (s.stato === "lavora") return { azione', "if (false) return { azione"),
    ("HZ18", "shared/volta/mods/arturo/sessioni.js", "if (s.vecchia) return { azione", "if (false) return { azione"),
    ("HZ18", "shared/volta/mods/arturo/sessioni.js", "|| argv.some((a) => dentro(a, s.id)))", ")"),
    ("HZ18", "shared/volta/mods/arturo/sessioni.js", '${id.replace(/[^\\w-]/g, "")}\\\\b`', '${id.replace(/[^\\w-]/g, "")}`'),
    ("HZ18", "shared/volta/mods/arturo/sessioni.js", "\\\\battach['\"]?\\\\s+['\"]?", "\\\\battach\\\\s+"),
    ("HZ19", "shared/volta/mods/arturo/barra.js", 'else if (c === "volta") this.volta.premiId(arg, cx);', ""),
    ("HZ19", "shared/volta/mods/arturo/volta.js", "if (!this.script) return null;", ""),
    ("HZ20", "shared/volta/mods/arturo/volta.js", 'exec(this.py, [this.script, "volta"', 'exec("python3", [this.script, "volta"'),
    ("HZ21", "shared/volta/installa-herdr.sh", "app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}",
     'if [ "$sistema" = windows ]; then app_home=${HERDR_APP_HOME:-${APPDATA:-$HOME/AppData/Roaming}/herdr-app}; '
     "else app_home=${HERDR_APP_HOME:-$HOME/.config/herdr-app}; fi"),
    ("HZ22", "shared/volta/installa-herdr.sh", '[ "$sistema" = mac-arm ] || { tasti=keys-ctrl.json; serie=keys-herdr.json; }', ":"),
    ("HZ22", "shared/volta/keys-ctrl.json", '"ctrl-shift-i": "arturo.note"', '"ctrl-shift-e": "arturo.note"'),
    ("HZ23", "shared/volta/installa-herdr.sh", 'if "$c" -c "import sys" >/dev/null 2>&1; then py=$c; break; fi',
     'if command -v "$c" >/dev/null 2>&1; then py=$c; break; fi'),
    ("HZ24", "shared/volta/mods/arturo/testata.js", "const scorciatoie = `${k.apri} cerca",
     "const scorciatoie = `⌘K cerca"),
    ("HZ25", "shared/volta/mods/arturo/suggerimenti.js", "else run(comandoSuggerimento(sug.id)); dopo?.(); })",
     "else { dopo?.(); run(comandoSuggerimento(sug.id)); } })"),
    ("HZ25", "shared/volta/mods/arturo/apri.js", '    if (r.tipo === "sessione") run(`arturo.volta-${chiaveSessione(r.s)}`);', '    if (r.tipo === "sessione") { this.chiudi(); run(`arturo.volta-${chiaveSessione(r.s)}`); }'),
    ("HZ26", "shared/volta/mods/arturo/nota.js", "const mainW = testata.larghezza - 2 * pad - (pannelloW ? pannelloW + gap : 0);",
     "const mainW = testata.larghezza - 2 * pad;"),
    ("HZ26", "shared/volta/mods/arturo/nota.js", "if (Math.abs(marchio.altezza + barra.altezza + piede.altezza - H) > 2) return null;", ""),
    ("HZ26", "shared/volta/mods/arturo/nota.js", "if (Math.abs(S + (m.divisore ?? 1) + testata.larghezza - W) > 2) return null;", ""),
    ("HZ26", "shared/volta/mods/arturo/main.js", "if (!MISURATE.has(this.nome) || !el?.on_size_change) return el;", "return el;"),
    ("HZ27", "shared/volta/mods/arturo/nota.js", "if (Number.isInteger(n.numero) && !tenuti.has(n.numero)) { tenuti.add(n.numero); return n; }", "return n;"),
    ("HZ27", "shared/volta/mods/arturo/nota.js", 'stato: "aperta", chiusa_quando: null', 'stato: "presa", chiusa_quando: null'),
    ("HZ27", "shared/volta/mods/arturo/nota.js", "n.punto.x * W / f.larghezza", "n.punto.x"),
    ("HZ27", "shared/volta/mods/arturo/nota.js", '"--note", riga, "--json", "--"', '"--note", riga, "--"'),
    ("HZ27", "shared/volta/mods/arturo/nota.js", "Per partire: arturo note mostra ${dati.id}", "Per partire: ${dati.id}"),
    ("HZ28", "shared/volta/mods/arturo/nota.js", "recente(b).localeCompare(recente(a))", "recente(a).localeCompare(recente(b))"),
    ("HZ28", "shared/volta/mods/arturo/nota.js", "numero: aperta ? n.numero : null", "numero: n.numero"),
    ("HZ28", "shared/volta/mods/arturo/nota.js", "  if (!prima) return [];\n", ""),
    ("HZ28", "shared/volta/keys.json", '"cmd-shift-e": "arturo.note"', '"cmd-shift-l": "arturo.note"'),
    ("HZ28", "shared/volta/mods/arturo/testata.js", ".on_click(() => apriElenco())", ""),
    ("HZ28", "shared/volta/mods/arturo/noteui.js", "run(`arturo.nota-${r.id}`);\n    this.chiudi();", "this.chiudi();\n    run(`arturo.nota-${r.id}`);"),
    ("HZ29", "bin/note_finestra.py", 'return {**n, "stato": "presa"}', "return n"),
    ("HZ29", "bin/note_finestra.py", 'presi = {n["numero"] for n in qui if n["numero"] is not None}', "presi = set()"),
    ("HZ29", "bin/note_finestra.py", 'sul_todo(n, ["fatto"] if stato == "risolta"', 'sul_todo(n, ["inizia"] if stato == "risolta"'),
    ("HZ29", "bin/note_finestra.py", "x = min(max(px - w // 2, 0), W - w)", "x = max(px - w // 2, 0)"),
    ("HZ29", "bin/note_finestra.py", "scala = W / f[\"larghezza\"] if f.get(\"larghezza\") else 1", "scala = 1"),
    ("HZ29", "bin/note_finestra.py", 'if n["stato"] not in APERTE:\n        raise ErroreNota(f"la nota {n[\'id\']} è già {n[\'stato\']}")\n    v = ', "v = "),
    ("HZ29", "bin/arturo", '    "note": ("note_finestra",', '    "notte": ("note_finestra",'),
    ("HZ30", "bin/note_finestra.py", "        if ora != letto:", "        if False:"),
    ("HZ31", "shared/volta/mods/arturo/notaui.js", "const r = await gestoNota(VERBI[che], n.id, testo);", "const r = { ok: true };"),
    ("HZ31", "shared/volta/mods/arturo/notaui.js", 'risolta: "risolvi"', 'risolta: "scarta"'),
    ("HZ31", "shared/volta/mods/arturo/dati.js", '"--chi", "federico", "--json"', '"--json"'),
    ("HZ31", "shared/volta/mods/arturo/dati.js", '...(t ? ["--", t] : [])', '...(t ? [t] : [])'),
    ("HZ31", "bin/note_finestra.py", 'if not testo and chi == "claude":', "if not testo:"),
    ("HZ32", "shared/volta/mods/arturo/nota.js", '{ id: "va-bene", etichetta: "Va bene così" }', '{ id: "va-bene", etichetta: "Va bene" }'),
    ("HZ32", "bin/note_finestra.py", '"presa": "Claude ci lavora", "risolta"', '"presa": "Presa", "risolta"'),
    ("HZ32", "bin/note_finestra.py", 'APERTE = ("aperta", "presa")', 'APERTE = ("aperta",)'),
    ("HZ32", "shared/volta/mods/arturo/nota.js", 'export const TIPO_PREDEFINITO = "correggere";', 'export const TIPO_PREDEFINITO = "domanda";'),
    ("HZ32", "bin/note_finestra.py", '"cwd": None, "testo_terminale": None}', '"cwd": None}'),
    ("HZ32", "docs/volta.md", "dice a chi l'ha scritta che ci lavori", "dice a Federico che ci lavori"),
    ("HZ09", "shared/volta/mods/arturo/dati.js", "Segui {radice}/shared/volta/trova-progetti.md", "Segui ~/.claude/shared/volta/trova-progetti.md"),
    ("HZ01", "shared/volta/installa-herdr.sh", '"radice": os.environ["ARTURO_RADICE"], ', ""),
    ("HZ33", "shared/volta/mods/arturo/dati.js", "const prompt = richiesta(sug.prompt, (await config()).radice);", "const prompt = sug.prompt;"),
    ("HZ33", "shared/volta/mods/arturo/dati.js", ": radiceDa(arturo[arturo.length - 1]),", ": `${home()}/.claude`,"),
    ("HZ33", "shared/volta/mods/arturo/dati.js", "[\\\\/]bin[\\\\/]arturo", "[/]bin[/]arturo"),
    ("HZ08", "hooks/session-start.sh", 'mkdir -p "$HOME/.claude/data" && date +%Y-%m-%d > "$HOME/.claude/data/herdr-invito"', ":"),
    ("HZ34", "shared/volta/mods/arturo/volta_sonda.py", 'for py in ("python3", "python"):', 'for py in ("python3",):'),
    ("HZ34", "shared/volta/mods/arturo/volta_sonda.py", 'return [v for v in voci if v.get("claude") or ("irraggiungibile" in v and (v["questa"] or v["host"] in viste))]', 'return voci'),
    ("HZ34", "shared/volta/mods/arturo/volta_sonda.py", 'sessioni += [dict(r, vecchia=True)', 'sessioni += [dict(r)'),
    ("HZ35", "shared/volta/volta-claude.sh", '[ "${CLAUDE_QUI:-0}" = 1 ] && qui_interattiva "$@"', ":"),
    ("HZ35", "shared/volta/volta-claude.sh", "  agents | attach | auth |", "  agentsX | attach | auth |"),
    ("HZ35", "shared/volta/volta-claude.sh", "grep -v '^Starting background service' | ", ""),
    ("HZ35", "shared/volta/volta-claude.sh", '[ -n "$senza_id" ] && qui_interattiva "$@"', ":"),
    ("HZ35", "shared/volta/volta-claude.sh", '[ -n "${HC_TERMINAL_ID:-}" ] && qui_interattiva "$@"', ":"),
    ("HZ35", "shared/volta/volta-claude.sh", 'printf \'Volta: la sessione non parte in background (%s). La apro qui, come prima.\\n\' "$motivo" >&2', "exit 1"),
    ("HZ36", "shared/volta/nascita.sh", "next } !dentro { print } END", "next } 1 { print } END"),
    ("HZ36", "shared/volta/nascita.sh", "END { exit dentro ? 3 : 0 }", "END { exit 0 }"),
    ("HZ36", "shared/volta/nascita.sh", "! typeset -f claude >/dev/null 2>&1; then", "true; then"),
    ("HZ36", "shared/volta/nascita.sh", "then printf '\\n' >> \"$1\"; fi", "then :; fi"),
    ("HZ36", "shared/volta/installa-herdr.sh", "&& ! printf '%s\\n' \"$stato_nascita\" | grep -q '^rifiutata'; then", "; then"),
    ("HZ36", "shared/volta/installa-herdr.sh", "if printf '%s\\n' \"$stato_nascita\" | grep -q '^assente' &&", "if false &&"),
    ("HZ36", "shared/volta/nascita.sh", 'rm -f "$NO" "$app/nascita-no"', ":"),
    ("HZ37", "shared/volta/nascita.sh", "    for f in $(tutti_i_file); do\n      if [ -f \"$f\" ] && grep -qF \"$INIZIO\" \"$f\"; then\n        if togli_da", "    for f in $(file_shell); do\n      if [ -f \"$f\" ] && grep -qF \"$INIZIO\" \"$f\"; then\n        if togli_da"),
    ("HZ37", "shared/volta/nascita.sh", "{ l = $0; sub(/\\r$/, \"\", l) } l == a { dentro = 1; next }", "{ l = $0 } l == a { dentro = 1; next }"),
    ("HZ37", "shared/volta/nascita.sh", "awk -v BINMODE=3 -v a=", "awk -v a=", "windows"),  # l'awk di Git per Windows toglie i \r
    ("HZ37", "shared/volta/nascita.sh", '      if utf16 "$f"; then say "NASCITA UTF16 $f"; continue; fi', "      :"),
    ("HZ37", "shared/volta/nascita.sh", '      mkdir -p "$(dirname "$f")"', "      :"),
    ("HZ37", "shared/volta/nascita.sh", 'case "$pol" in Restricted | AllSigned) say', 'case "$pol" in Nessuna) say'),
    ("HZ38", "shared/volta/nascita.sh", "and -not (Get-Command claude -CommandType Function -ErrorAction SilentlyContinue)) {", ") {"),
    ("HZ37", "shared/volta/installa-herdr.sh", '[ "$sistema" = windows ] && cp "$qui/volta-claude.ps1"', '[ "$sistema" = nessuno ] && cp "$qui/volta-claude.ps1"'),
    ("HZ38", "shared/volta/volta-claude.ps1", "if ($env:CLAUDE_QUI -eq '1') { Qui }", "#"),
    ("HZ38", "shared/volta/volta-claude.ps1", "if ($senzaId) { Qui }", "#"),
    ("HZ38", "shared/volta/volta-claude.ps1", "$_ -and $_ -notmatch '^Starting background service'", "$_"),
    ("HZ39", "shared/volta/mods/arturo/volta_sonda.py", "\n        if rc != 0 and (non_parte(out, err) or rc == 9009):", "\n        if True:"),  # quella di nasci, non di servizio
    ("HZ40", "shared/volta/mods/arturo/volta_sonda.py", '        rc, out, err = lancia(hc() + ["exec", "--on", nome, "--timeout", str(t - 5)] + prog + args, timeout=t)', '        rc, out, err = lancia(hc() + ["exec", nome, "--timeout", str(t - 5)] + prog + args, timeout=t)'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '    for prog in (["claude"], ["python3", "-c", codice], ["python", "-c", codice]):', '    for prog in (["claude"],):'),
    ("HZ41", "shared/volta/mods/arturo/volta_sonda.py", '            primo = primo or (rc, out, err)\n            continue', '            primo = primo or (rc, out, err)\n            break'),
    ("HZ40", "shared/volta/mods/arturo/volta_sonda.py", '    if not ID.fullmatch(sid or ""):  # mai', "    if False:  # mai"),
    ("HZ40", "shared/volta/mods/arturo/volta_sonda.py", "    if verbo not in VERBI:", "    if False:"),
    ("HZ40", "shared/volta/mods/arturo/volta_sonda.py", '            if fin == "G":\n                c = n - 1', '            if fin == "G":\n                pass'),
    ("HZ40", "shared/volta/mods/arturo/volta_sonda.py", "    fuori = (\"Checking for updates\",)", "    fuori = (\"zzz\",)"),
    ("HZ40", "shared/volta/mods/arturo/sessioni.js", 'if (s.stato === "lavora" || s.stato === "aspetta") out.push', 'if (s.stato === "lavora") out.push'),
    ("HZ40", "shared/volta/mods/arturo/sessioni.js", "  if (!prima) return [];", "  if (!prima) prima = { sessioni: [] };"),
    ("HZ40", "shared/volta/mods/arturo/sessioni.js", "if (!s.id || s.vecchia) continue;", "if (!s.id) continue;"),
    ("HZ40", "shared/volta/mods/arturo/sessioni.js", 'out.push({ verbo: "rm", testo: "Elimina", conferma: "Sì, elimina" })', 'out.push({ verbo: "rm", testo: "Elimina" })'),
    ("HZ39", "shared/volta/mods/arturo/volta_sonda.py", 'dati = {"prompt": prompt or "", "progetto": progetto}', 'dati = {"prompt": "", "progetto": progetto}'),
    ("HZ39", "shared/volta/mods/arturo/volta_sonda.py", 'if m["stato"] not in (None, "connected"):', "if False:"),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'return nasciSu(soloQui ? "qui" : dove(), prompt, null);', 'return nasciSu(dove(), prompt, null);'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'return typeof d === "string" && altreMacchine().some((m) => m.host === d) ? d : "qui";', 'return typeof d === "string" && d ? d : "qui";'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'return nasciSu(sua ?? d, prompt, nome);', 'return nasciSu("qui", prompt, nome);'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'const v = await apriSessione({ id: nata.id, sessionId: nata.sessionId, nome, progetto, questa: macchina === "qui", host: macchina }, nata.attach, true);', "const v = {};"),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'questa: macchina === "qui", host: macchina }, nata.attach, true);', 'questa: macchina === "qui", cartella: "/base", host: macchina }, nata.attach, true);'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'return s.status ?? statoAgganciata(schedaAgganciata(s));', 'return s.status ?? null;'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'return s.status ?? statoAgganciata(schedaAgganciata(s));', 'return statoAgganciata(schedaAgganciata(s)) ?? s.status;'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'if (v?.host === "qui") out[id] = v.stato;', 'out[id] = v.stato;'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", "(b.tab === attiva) - (a.tab === attiva)", "0"),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'if (statoAgganciata(g) === "blocked") return notify', 'if (false) return notify'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'const g = a || !s ? null : schedaAgganciata(s);', 'const g = null;'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'stato: statoSpazio(s)', 'stato: s?.status ?? null'),
    ("HZ39", "shared/volta/mods/arturo/testata.js", 'const st = statoScheda(s, tab);', 'const st = s?.status;'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'const volta = g && g.tab === tab?.id ? statoAgganciata(g) : null;', 'const volta = null;'),
    ("HZ39", "shared/volta/mods/arturo/todo.js", 'statoSpazio(spazio(p))', 'spazio(p)?.status'),
    ("HZ39", "shared/volta/mods/arturo/todo.js", '    const st = statoSpazio(s);', '    const st = s.status;'),
    ("HZ39", "shared/volta/mods/arturo/barra.js", '`|${JSON.stringify(statiQui())}|', '`|'),
    ("HZ39", "shared/volta/mods/arturo/volta_sonda.py", 'app = os.environ.get("HERDR_APP_HOME") or ', "app = "),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'const args = [c.volta, copia ? copia.verbo : "nasci", macchina,', 'const args = [`${appHome()}/mods/arturo/volta_sonda.py`, copia ? copia.verbo : "nasci", macchina,'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", "const g = a ? null : schedaAgganciata(s);", "const g = null;"),
    ("HZ39", "shared/volta/mods/arturo/dati.js", "if (id) return { terminal: p.terminal, tab: p.tab, id };", "if (false) return { terminal: p.terminal, tab: p.tab, id };"),
    ("HZ39", "shared/volta/mods/arturo/dati.js", 'if (sug.dove === "nuova") return nuova(prompt, true);', 'if (sug.dove === "nuova") return nuova(prompt);'),
    ("HZ39", "shared/volta/mods/arturo/dati.js", "if (!a && !g) return nuova(prompt, true);", "if (!a && !g) return nuova(prompt);"),
    ("HZ39", "shared/volta/mods/arturo/testata.js", ".when(Boolean(nasceSu(t)), (el) => el.child(nasceSu(t)));", ";"),
    ("HZ34", "shared/volta/mods/arturo/dati.js", "`${appHome()}/mods/arturo/volta_sonda.py`", "`${home()}/.claude/scripts/teletrasporto.py`"),
    ("HZ34", "shared/volta/mods/arturo/volta.js", "esiste(c.volta)", "esiste(`${home()}/x/volta_sonda.py`)"),
    ("HZ44", "shared/volta/mods/arturo/volta_sonda.py", 'sessioni = agenti(["--all"])', "sessioni = agenti([])"),
    ("HZ44", "shared/volta/mods/arturo/volta_sonda.py", '    if (s.get("startedAt") or 0) >= soglia:\n        return True', "    if True:\n        return True"),
    ("HZ44", "shared/volta/mods/arturo/volta_sonda.py", "    sessioni = agenti([])\n", "    sessioni = None\n"),
    ("HZ44", "shared/volta/mods/arturo/barra.js", 'else if (c === "volta-altro") this.volta.altroId(arg, cx);', ""),
    ("HZ44", "shared/volta/mods/arturo/comandi.js", '  if (c.startsWith("volta-altro-")) return { verbo: "volta-altro", arg: dopo("volta-altro-"), lungo: false };\n', ""),
    ("HZ44", "shared/volta/mods/arturo/volta.js", "this.menu = chiave(s);\n    this.scopri(s);\n    this.fare(s, a, cx);", "this.menu = chiave(s);"),
    ("HZ44", "shared/volta/mods/arturo/volta.js", 'if (g && s.stato === "ferma") this.aperti[g.chiave] = true;', ""),
    ("HZ45", 'hooks/titolo-sessione.py', '        if salvato.get("titolo"):\n            return 0\n', ''),
    ("HZ45", 'hooks/titolo-sessione.py', 'vuole_titolo = not persona and not (modello and (adesso - float(salvato.get("quando") or 0) < ogni', 'vuole_titolo = not persona and not (modello and (False'),
    ("HZ45", 'hooks/titolo-sessione.py', '                                                     or peso <= int(salvato.get("peso") or 0)))', '                                                     or False))'),
    ("HZ45", 'hooks/titolo-sessione.py', '    if not etichette and len(righe) == 1:\n', '    if not etichette:\n'),
    ("HZ45", 'hooks/titolo-sessione.py', '    return t if 2 <= len(t) <= LUNGO else ""', '    return t'),
    ("HZ45", 'hooks/titolo-sessione.py', 'if os.environ.get("ARTURO_TITOLI") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):', 'if os.environ.get("ARTURO_TITOLO_FIGLIO"):'),
    ("HZ45", 'hooks/titolo-sessione.py', 'if os.environ.get("ARTURO_TITOLI") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):', 'if os.environ.get("ARTURO_TITOLI") == "0":'),
    ("HZ45", 'hooks/titolo-sessione.py', 'env = dict(os.environ, ARTURO_TITOLO_FIGLIO="1", ', 'env = dict(os.environ, '),
    ("HZ45", 'hooks/titolo-sessione.py', '"--settings", \'{"disableAllHooks":true}\', ', ''),
    ("HZ45", 'hooks/titolo-sessione.py', '    return r.stdout if r.returncode == 0 else ""', '    return r.stdout or "Titolo di ripiego"'),
    ("HZ45", 'hooks/titolo-sessione.py', ' or d.get("isMeta"):', ':'),
    ("HZ45", 'hooks/titolo-sessione.py', '        if " -- " in resto:\n            resto = resto.split(" -- ", 1)[1]\n', ''),
    ("HZ45", 'shared/volta/mods/arturo/volta_sonda.py', '            s["titolo"] = t.strip()[:80]', '            pass'),
    ("HZ45", 'shared/volta/mods/arturo/sessioni.js', '  if (scritto) return scritto;\n', ''),
    ("HZ45", 'shared/volta/mods/arturo/volta.js', '=== "macchina" ? "macchina" : "progetto"', '=== "progetto" ? "progetto" : "macchina"'),
    ("HZ45", "shared/volta/mods/arturo/volta.js", "(s.titolo ? div().whitespace_normal() : div().truncate())", "div().truncate()"),
    ("HZ46", "shared/volta/mods/arturo/volta_sonda.py", 'tx[:400].rsplit(None, 1)[0] + "\\u2026"', 'tx[:400]'),
    ("HZ46", "shared/volta/mods/arturo/volta_sonda.py", '"risposta": (s.get("risposta") or "")[:420],', '"risposta": (s.get("risposta") or "")[:200],'),
    ("HZ46", "shared/volta/mods/arturo/sessioni.js", '.replace(/^\\s*(#+|>)\\s*/, "")', ''),
    ("HZ46", "shared/volta/mods/arturo/sessioni.js", 'const senzaSegni = (r) => r.replace(/\\*\\*|`/g, "")', 'const senzaSegni = (r) => r.replace(/[*_`]/g, "")'),
    ("HZ46", "shared/volta/mods/arturo/sessioni.js", '  return out.length ? out : null;', '  return out;'),
    ("HZ46", "shared/volta/mods/arturo/sessioni.js", '.replace(/:$/, "")', ''),
    ("HZ46", "shared/volta/mods/arturo/volta.js", '    if (a.verbo === "logs" && anteprima(s)) { this.anteprime[k] = true; return cx.notify(); }\n', ''),
    ("HZ46", "shared/volta/mods/arturo/volta.js", ': div().id(id).whitespace_normal().text_size(12.5)', ': div().id(id).truncate().text_size(12.5)'),
    ("HZ47", "shared/volta/mods/arturo/volta.js", "      .when(Boolean(avviso) && !aperto, (el)", "      .when(aperto, (el) => el.child(this.gesti(t, s, az)))\n      .when(Boolean(avviso) && !aperto, (el)"),
    ("HZ47", "shared/volta/mods/arturo/volta.js", "\n      .when(Boolean(gesti), (el) => el.child(gesti.mb(10)));", ";"),
    ("HZ47", "shared/volta/mods/arturo/volta.js", "const gesti = this.pannello(t);", "const gesti = null;"),
    ("HZ47", "shared/volta/mods/arturo/volta.js", "      .child(this.gesti(t, s, az))\n      .when(Boolean(avviso), (el)", "      .when(Boolean(avviso), (el)"),
    ("HZ47", "shared/volta/mods/arturo/volta.js", ".when(Boolean(avviso) && !aperto, (el)", ".when(Boolean(avviso), (el)"),
    ("HZ48", "shared/volta/mods/arturo/volta_sonda.py", 'lavoro = s.get("id") if fondo else None', "lavoro = None"),
    ("HZ48", "shared/volta/mods/arturo/volta_sonda.py", 'corto = lavoro if isinstance(lavoro, str)', 'corto = sid[:8] if isinstance(lavoro, str)'),
    ("HZ49", "shared/volta/mods/arturo/volta.js", 'const xa = xRiga(s);', 'const xa = null;'),
    ("HZ49", "shared/volta/mods/arturo/volta.js", "const vediX = Boolean(xa) && (this.sopra === k || chiedoX || faccioX);", "const vediX = Boolean(xa);"),
    ("HZ49", "shared/volta/mods/arturo/volta.js", ".on_click((_e, cx) => this.fare(s, xa, cx))", ""),
    ("HZ50", "shared/volta/mods/arturo/barra.js", ' nuova · ${tasti().elenco} elenco`, () => apriElenco()', ' nuova · ${tasti().elenco} elenco`, () => apriGuida()'),
    ("HZ50", "shared/volta/layouts/arturo.json", '"px": 44', '"px": 156'),
    ("HZ51", "shared/volta/mods/arturo/sessioni.js", "].sort((a, b) => tempo(b) - tempo(a) || titolo(a)", "].sort((a, b) => tempo(a) - tempo(b) || titolo(a)"),
    ("HZ51", "shared/volta/mods/arturo/sessioni.js", "    out.sort((a, b) => recente(b) - recente(a) || a.titolo.localeCompare(b.titolo));\n", ""),
    ("HZ51", "shared/volta/mods/arturo/sessioni.js", ".filter((g) => g.sessioni.length)).sort((a, b) => recente(b) - recente(a));", ".filter((g) => g.sessioni.length));"),
    ("HZ51", "shared/volta/mods/arturo/sessioni.js", "const recente = (g) => Math.max(0, ...g.sessioni.map(tempo));", "const recente = (g) => Math.min(...g.sessioni.map(tempo));"),
    ("HZ51", "shared/volta/mods/arturo/volta_sonda.py", '"ultimo": s.get("ultimo") or nascita(s),', '"ultimo": s.get("ultimo") or "",'),
    ("HZ51", "shared/volta/mods/arturo/volta_sonda.py", "time.gmtime(t / 1000))", "time.gmtime(t))"),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', 'const etichetta = l.filter((x) => dice(x) === true);', 'const etichetta = [];'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', 'for (const x of schede) if (!(await nuda(x.address))) { scheda = x; break; }', 'for (const x of schede) { scheda = x; break; }'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', 'f.pid === d.pid && JSON.stringify(f.argv) !== JSON.stringify(d.argv);', 'f.pid === d.pid;'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', 'const a = await prepara(s, s.stato === "errore");', 'const a = await prepara(s, false);'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '  if (!pronta) {', '  if (true) {'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '    if (a.errore) return { errore: `Non la apro: ${a.errore}.` };\n', ''),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '  if (riavviata || m?.fermo) return fallita(m);\n', ''),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '  if (!(await nuda(indirizzo))) return {};\n  const fallita', '  const fallita'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '    run("space.select", { id: sp.id });\n    run("tab.new", { name: nome, space: sp.id, folder: cartella, argv: argvScheda(argv) });', '    const tab = sp.tabs.find((tb) => tb.name === nome);\n    if (tab) return run("tab.select", { id: tab.id });\n    run("tab.new", { name: nome, space: sp.id, folder: cartella, argv: argvScheda(argv) });'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '(/^[\\w@%+=:,./-]+$/.test(x) ? x', '(true ? x'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '!libero(s.name) ? canonico(s.name) : null;', '!libero(s.name) ? canonico(s.name) : canonico(s.name);'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', '    if (scheda) await etichetta(scheda, s);\n  }\n  return { come: rilancia', '  }\n  return { come: rilancia'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', 'const r = await hc(["send", scheda.address, comando(argvScheda(argv))]);', 'const r = { code: 0 };'),
    ('HZ52', 'shared/volta/mods/arturo/sessioni.js', 'return [a[0], "-t", ...OPZIONI_SSH, ...a.slice(2)];', 'return a;'),
    ('HZ52', 'shared/volta/mods/arturo/dati.js', 'return nasciSu(dove(), "", progetto, "Nuova sessione");', 'return nasciSu(dove(), "", progetto);'),
    ('HZ52', 'shared/volta/mods/arturo/volta.js', '      if (v?.errore) this.nonApre(s, v.errore, cx);\n', ''),
    ('HZ19', 'shared/volta/mods/arturo/volta.js', 'if (d.azione === "aggancia") return this.apri(s, d.argv, false, cx);', 'if (d.azione === "aggancia") return this.apri(s, d.argv, true, cx);'),
    ('HZ53', 'shared/volta/mods/arturo/volta_sonda.py', '    if riavvia:\n        r = azione(nome, "respawn", sid)', '    if False:\n        r = azione(nome, "respawn", sid)'),
    ('HZ53', 'shared/volta/mods/arturo/volta_sonda.py', '    if ID.fullmatch(sid or "") is None:', '    if False:'),
    ('HZ53', 'shared/volta/mods/arturo/volta_sonda.py', '        return {"ok": True, "riavviata": True}\n    s = servizio(nome)', '        return {"ok": True, "riavviata": True}\n    s = {}'),
    ('HZ53', 'shared/volta/mods/arturo/volta_sonda.py', '        if not r.get("ok"):\n            return {"errore": "non si riavvia: %s"', '        if False:\n            return {"errore": "non si riavvia: %s"'),
    ('HZ53', 'shared/volta/keys.json', '"cmd-t": "arturo.casa"', '"cmd-t": "arturo.volta-nuova"'),
    ('HZ53', 'shared/volta/keys-ctrl.json', '"ctrl-shift-t": "arturo.casa"', '"ctrl-shift-y": "arturo.casa"'),
    ('HZ53', 'shared/volta/installa-herdr.sh', 'if k in mia and mia[k] != v and mia[k] not in PRENDE.get(v, ()):', 'if k in mia and mia[k] != v:'),
    ('HZ53', 'shared/volta/installa-herdr.sh', '"arturo.casa": ("tab.new", "arturo.volta-nuova"),', '"arturo.casa": ("tab.new",),'),
    ('HZ53', 'shared/volta/installa-herdr.sh', 'mia[k] not in PRENDE.get(v, ()):', 'v not in PRENDE:'),
    ('HZ53', 'shared/volta/mods/arturo/barra.js', '    else if (c === "volta-nuova") this.lungo(c, cx, () => nuovaScheda());\n', ''),
    ('HZ22', 'shared/volta/installa-herdr.sh', 'PRENDE = {"arturo.casa": ("tab.new", "arturo.volta-nuova"),', 'PRENDE = {'),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', 'if (s.tipo === "background" && !chiusa(s) && s.stato !== "errore") out.push({ verbo: "chiudi", testo: "Chiudi con /fine" });', 'out.push({ verbo: "chiudi", testo: "Chiudi con /fine" });'),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', '  if (rm) return { ...rm, aiuto: "Elimina la sessione" };\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', '  if (s.progetto) out.push({ verbo: "contesto", testo: "Contesto del progetto" });\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', 'if (!s || s.vecchia) return [];\n  const out = [{ verbo: "apri"', 'if (!s) return [];\n  const out = [{ verbo: "apri"'),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', 'return out.concat(azioni(s).filter((a) => a.verbo !== "stop"));', 'return out.concat(azioni(s));'),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', '.slice(0, 53).trim()} (fork)`', '.slice(0, 53).trim()} (copia)`'),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', '`${titolo(s).slice(0, 53).trim()} (fork)`', '`${titolo(s)} (fork)`'),
    ('HZ54', 'shared/volta/mods/arturo/sessioni.js', '{ verbo: "duplica", testo: "Duplica" }, { verbo: "fork", testo: "Fork" },', '{ verbo: "duplica", testo: "Duplica" },'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', '...(copia?.verbo === "fork" ? [copia.sessionId] : []),', ''),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', '...(copia?.cartella ? ["--cartella", copia.cartella] : []),', ''),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', '...(copia?.titolo ? ["--titolo", copia.titolo] : []),', ''),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', 'if (!copia) notify({ title: titolo, body: errore, level });', 'notify({ title: titolo, body: errore, level });'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', 'return nasciSu(s.host ?? "qui", "", s.progetto', 'return nasciSu(dove(), "", s.progetto'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', '{ verbo: fork ? "fork" : "duplica", sessionId: s.sessionId,', '{ verbo: fork ? "fork" : "duplica", sessionId: s.id,'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', 'fork ? titoloFork(s).slice(0, 40) : "Nuova sessione",', '"Nuova sessione",'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', 'if (panes().filter((x) => x.tab === p.tab).length === 1) run("tab.close", { id: p.tab, confirmed: true });', 'if (true) run("tab.close", { id: p.tab, confirmed: true });'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', 'run("tab.close", { id: p.tab, confirmed: true });', 'run("tab.close", { id: p.tab });'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', '    else run("terminal.kill", { terminal: t.address });\n', '    else run("tab.close", { id: p.tab });\n'),
    ('HZ54', 'shared/volta/mods/arturo/dati.js', '      return v.errore ? dico("La sessione è nata, ma non si apre", v.errore) : { ok: true, id: nata.id };\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/volta.js', '      .on_mouse_down("right", (_e, cx) => { if (apriMenuSessione(s)) cx.stop_propagation(); })\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/volta.js', '    if (SOLO_MENU.has(verbo)) return this.fare(s, a, cx);\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/volta.js', '    if (a.verbo === "apri") return this.premi(s, cx);\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/volta.js', '    chiudiSchede(s);\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/volta.js', 'a.verbo === "duplica" || a.verbo === "fork" ? await copiaSessione(s, a.verbo)', 'false ? await copiaSessione(s, a.verbo)'),
    ('HZ54', 'shared/volta/mods/arturo/volta.js', '      : lavoro ? { testo: lavoro, colore: "working" } : dettaglio(s, modo);', '      : dettaglio(s, modo);'),
    ('HZ54', 'shared/volta/mods/arturo/volta.js', 'const voci = menu(s).concat(azioni(s).filter((x) => x.verbo === "stop"));', 'const voci = azioni(s);'),
    ('HZ54', 'shared/volta/mods/arturo/barra.js', '    else if (c === "volta-menu") this.volta.menuId(arg);\n', ''),
    ('HZ54', 'shared/volta/mods/arturo/main.js', 'sessione: MenuSessione, ', ''),
    ('HZ54', 'shared/volta/mods/arturo/menusessione.js', '    run(comandoGesto(this.s, v));\n    this.chiudi();', '    this.chiudi();\n    run(comandoGesto(this.s, v));'),
    ('HZ54', 'shared/volta/mods/arturo/menusessione.js', '`arturo.volta-gesto-${v.verbo}-${chiaveSessione(s)}`', '`arturo.volta-fai-${v.verbo}-${chiaveSessione(s)}`'),
    ('HZ54', 'shared/volta/mods/arturo/menusessione.js', 'props: { parte: "sessione", sessione: s }, kind: "popup", width: 230', 'props: { parte: "sessione", sessione: s }, kind: "dialog", width: 230'),
    ('HZ54', 'shared/volta/mods/arturo/menusessione.js', 'this.voci = menu(this.s);', 'this.voci = [];'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', 'argv += ["--resume", a["riprendi"]] + ([] if a.get("stessa") else ["--fork-session"])', 'argv += ["--resume", a["riprendi"]]'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', 'if a.get("riprendi") and not qui:', 'if False:'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', 'if qui:\n    base = cartella', 'if False:\n    base = cartella'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', 'qui = bool(cartella) and os.path.isdir(cartella)', 'qui = bool(cartella)'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', 'nome = str(a.get("nome") or "").lstrip("-").strip()[:60]', 'nome = str(a.get("nome") or "").strip()[:60]'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', 'if riprendi is not None and not ID.fullmatch(riprendi or ""):', 'if False:'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', '(("cartella", cartella), ("riprendi", riprendi), ("nome", titolo), ("stessa", stessa))', '(("cartella", cartella), ("riprendi", None), ("nome", titolo), ("stessa", stessa))'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', '("riprendi", riprendi), ("nome", titolo), ("stessa", stessa)) if v})', '("riprendi", riprendi), ("nome", None), ("stessa", stessa)) if v})'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', '        esito = nasci(resto[0], prompt, opz.get("progetto"), opz.get("cartella"))\n', '        esito = nasci(resto[0], prompt, opz.get("progetto"))\n'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', '        esito = nasci(resto[0], "", opz.get("progetto"), opz.get("cartella"), resto[1], opz.get("titolo"))', '        esito = nasci(resto[0], "", None, opz.get("cartella"), resto[1], opz.get("titolo"))'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', '    if argv and argv[0] in COPIE:\n', '    if False:\n'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', '    attesi = 2 if verbo == "fork" else 1\n', '    attesi = len(resto)\n'),
    ('HZ55', 'shared/volta/mods/arturo/volta_sonda.py', 'argv += ["-n", nome]', 'argv += [nome]'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", 'nuovo = {"titolo": valore, "fonte": "persona", "quando": time.time(), "peso": 0, "portato": False}', 'nuovo = {"titolo": valore, "fonte": "avvio", "quando": time.time(), "peso": 0, "portato": False}'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", 'progetto=valore, fonte="persona", quando=time.time(),\n', 'progetto=valore, quando=time.time(),\n'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", 'nuovo = dict(prima or {"stato": "nuova"}, progetto=valore,', 'nuovo = dict({"stato": "nuova"}, progetto=valore,'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", 'inizio=prima.get("inizio", True) if stesso else False)', 'inizio=True)'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", 'inizio=prima.get("inizio", True) if stesso else False)', 'inizio=False)'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", 'if prima.get("fonte") != "persona" or prima.get("progetto") != valore:\n            esci(ok=True, progetto=', 'if prima.get("fonte") != "persona":\n            esci(ok=True, progetto='),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '            if fonte == "persona" and scheda.get("inizio") is False:', '            if fonte == "persona":'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '                "daIniziare": s.get("daIniziare") if isinstance(s.get("daIniziare"), str) else None,\n', ''),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '    segno = "--portato" if verbo == "rinomina" else "--iniziato"', '    segno = "--portato"'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '        if prima.get("fonte") != "persona" or (valore and prima.get("titolo") != valore):', '        if prima.get("fonte") != "persona":'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '        nuovo = dict(prima, portato=True)', '        nuovo = dict(prima)'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '        if prima.get("fonte") == "persona":\n            os.remove(f)', '        if True:\n            os.remove(f)'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '        if prima.get("fonte") == "persona":\n            os.remove(f)', '        if False:\n            os.remove(f)'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '        if not SLUG.fullmatch(valore or ""):', '        if not valore:'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '    if verbo not in CAMBI:\n        return {"errore": "cambio sconosciuto: %s" % verbo}\n    if not ID.fullmatch(sid or ""):', '    if False:'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '        valore = nome_pulito(valore)\n    # `portato`', '        pass\n    # `portato`'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '    if argv and argv[0] in CAMBI:\n', '    if False:\n'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '            if tit.get("fonte") == "persona" and not tit.get("portato"):', '            if tit.get("fonte") == "persona":'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '            if tit.get("fonte") == "persona" and not tit.get("portato"):', '            if not tit.get("portato"):'),
    ("HZ58", "shared/volta/mods/arturo/volta_sonda.py", '                "daPortare": s.get("daPortare") if isinstance(s.get("daPortare"), str) else None,\n', ''),
    ("HZ58", "hooks/titolo-sessione.py", '    vuole_titolo = not persona and not (', '    vuole_titolo = not ('),
    ("HZ58", "hooks/titolo-sessione.py", '            if leggi(f).get("fonte") == "persona" and viva(f.stem):\n                continue\n', ''),
    ("HZ58", "hooks/titolo-sessione.py", '            if leggi(f).get("fonte") == "persona" and viva(f.stem):', '            if leggi(f).get("fonte") == "persona":'),
    ("HZ58", "hooks/titolo-sessione.py", '            if adesso - f.stat().st_mtime <= VECCHIO:\n                continue\n', ''),
    ("HZ58", "hooks/scheda-terminale.py", '    persona = salvato.get("fonte") == "persona" and bool(salvato.get("progetto"))', '    persona = False'),
    ("HZ58", "hooks/scheda-terminale.py", 'progetto, fonte = ("", "") if persona else (progetto_da_prompt(', 'progetto, fonte = (progetto_da_prompt('),
    ("HZ58", "hooks/scheda-terminale.py", '    if not progetto and evento == "PostToolUse" and not persona:', '    if evento == "PostToolUse":'),
    ("HZ58", "hooks/scheda-terminale.py", '        if not persona:\n            try:\n                f.unlink()', '        if True:\n            try:\n                f.unlink()'),
    ("HZ58", "hooks/scheda-terminale.py", '        if not persona:\n            try:\n                f.unlink()', '        if False:\n            try:\n                f.unlink()'),
    ("HZ54", "shared/volta/mods/arturo/sessioni.js", '  out.push({ verbo: "rinomina", testo: "Rinomina…" });\n', ''),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '.replace(/\\s+/g, " ").trim().slice(0, 60).trim();', '.trim();'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '.normalize("NFD").replace(/[\\u0300-\\u036f]/g, "")\n', '\n'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '.padStart(4, "0")).join("");', ').join("");'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '  if (m[1] === "progetto" && !valore) return null;\n', ''),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", 'const valore = m[1] === "nome" ? nomeNuovo(decodifica(m[2])) : progettoNuovo(decodifica(m[2]));', 'const valore = decodifica(m[2]);'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '/^volta-cambia-(nome|progetto)-((?:[0-9a-f]{4})*)-(.+)$/', '/^volta-cambia-(\\w+)-((?:[0-9a-f]{4})*)-(.+)$/'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '`arturo.volta-cambia-${cosa}-${codifica(valore)}-${chiave(s)}`', '`arturo.volta-cambia-${cosa}-${codifica(valore)}-${s.sessionId}`'),
    ("HZ120", "shared/volta/mods/arturo/sessioni.js", '`arturo.volta-cambia-${cosa}-${codifica(valore)}-${chiave(s)}`', '`arturo.volta-cambia-${cosa}-${codifica(valore)}-${s.id}`'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '    if (k) visti.add(k);', '    visti.add(k);'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '  return [...visti].sort((a, b) => a.localeCompare(b));', '  return [...visti];'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '[...l.filter((p) => nomi(p).some((x) => x.startsWith(f))), ...l.filter((p) => !nomi(p).some((x) => x.startsWith(f)) && nomi(p).some((x) => x.includes(f)))] : l;', 'l.filter((p) => nomi(p).some((x) => x.includes(f))) : l;'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '  if (dentro.length !== 1 || !["\\u276f", ">"].includes(dentro[0][0])) return false;', '  if (!dentro.length) return false;'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '  return t === "" || /^Try ".*"$/.test(t);', '  return true;'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '  if (bordi.length < 2) return false;', '  if (bordi.length < 2) return true;'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '(s && !s.vecchia && s.stato === "ferma" && typeof s.daPortare', '(s && !s.vecchia && typeof s.daPortare'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", '(s && !s.vecchia && s.stato === "ferma" && typeof s.daPortare', '(s && s.stato === "ferma" && typeof s.daPortare'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", 'cosa === "nome" ? "rinomina" : "progetto", s.host ?? "qui", s.sessionId, ...opzioni,', 'cosa === "nome" ? "rinomina" : "progetto", s.host ?? "qui", s.id, ...opzioni,'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", 'cosa === "nome" ? "rinomina" : "progetto", s.host ?? "qui", s.sessionId, ...opzioni,', 'cosa === "nome" ? "rinomina" : "progetto", "qui", s.sessionId, ...opzioni,'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '      ...(valore ? ["--", valore] : [])], { timeout: 90000 });', '      "--", valore], { timeout: 90000 });'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '    if (!p || panes().filter((x) => x.tab === p.tab).length !== 1) continue;', '    if (!p) continue;'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", 'run("tab.rename", { id: p.tab, name: String(nome).slice(0, 40) });', 'run("tab.rename", { id: p.tab, name: String(nome) });'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '    if (await nuda(a)) continue;\n', ''),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '      if (schermo.code !== 0 || !casellaVuota(schermo.stdout)) continue;', '      if (schermo.code !== 0) continue;'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '      scritto = r.code === 0;', '      scritto = true;'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '  if (!scritto) return false;\n', ''),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '    } catch { /* si prova la scheda dopo */ }\n    break;\n', '    } catch { /* si prova la scheda dopo */ }\n'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", 'const esito = await cambiaSessione(s, "nome", nome, ["--portato"]);', 'const esito = { ok: true };'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", 'const scriviNome = (s, nome) => scriviComando(s, `/rename ${nome}`);', 'const scriviNome = (s, nome) => scriviComando(s, nome);'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", 'if (terminaliDi(s).length) come = (await scriviComando(s, `/inizio ${slug}`)) ? "scheda" : null;', 'if (terminaliDi(s).length) come = (await scriviComando(s, slug)) ? "scheda" : null;'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '    else if (!ripresa) return { fatto: false };\n', ''),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '  const esito = await cambiaSessione(s, "progetto", slug, ["--iniziato"]);', '  const esito = await cambiaSessione(s, "progetto", slug, []);'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", 'export const daIniziare = (s) => (s && !s.vecchia && s.stato === "ferma" && typeof s.daIniziare === "string"', 'export const daIniziare = (s) => (s && !s.vecchia && typeof s.daIniziare === "string"'),
    ("HZ54", "shared/volta/mods/arturo/dati.js", '  if (progetto && !prompt && copia?.verbo !== "fork") prompt = `/inizio ${progetto}`;', '  if (progetto && !prompt) prompt = `/inizio ${progetto}`;'),
    ("HZ54", "shared/volta/mods/arturo/dati.js", '  if (progetto && !prompt && copia?.verbo !== "fork") prompt = `/inizio ${progetto}`;', ''),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '  if (s.tipo !== "background" || !Array.isArray(s.attach)) return s.terminale ? { resta: true } : {};', '  if (!Array.isArray(s.attach) && !s.terminale) return {};'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", '  if (!chiudiSchede(s)) return {};', '  chiudiSchede(s);'),
    ("HZ59", "shared/volta/mods/arturo/dati.js", 'const r = await apriSessione({ ...s, progetto }, s.attach);', 'const r = await apriSessione(s, s.attach);'),
    ("HZ59", "shared/volta/mods/arturo/volta.js", '    if (verbo in CAMBIA) return this.chiedi(s, CAMBIA[verbo]);\n', ''),
    ("HZ59", "shared/volta/mods/arturo/volta.js", 'return e?.click_count >= 2 ? this.chiedi(s, "nome") : this.premi(s, cx);', 'return this.premi(s, cx);'),
    ("HZ59", "shared/volta/mods/arturo/volta.js", '    this.portaNomi();\n', ''),
    ("HZ59", "shared/volta/mods/arturo/volta.js", '    this.portaInizi();\n', ''),
    ("HZ59", "shared/volta/mods/arturo/volta.js", 'portaInizio(s, this.spostate[k] === s.daIniziare)', 'portaInizio(s, true)'),
    ("HZ59", "shared/volta/mods/arturo/volta.js", 'if (r.ok && cosa === "progetto" && r.iniziato === false) this.spostate[k] = valore;', ''),
    ("HZ59", "shared/volta/mods/arturo/volta.js", '      if (!daPortare(s) || this.porto[k]) continue;', '      if (!daPortare(s)) continue;'),
    ("HZ59", "shared/volta/mods/arturo/volta.js", '        if (r.ok && cosa === "nome" && valore) rinominaSchede(s, valore);\n', ''),
    ("HZ59", "shared/volta/mods/arturo/volta.js", 'String(s.progetto ?? "") !== valore) dopo = await spostaScheda(s, valore);', 'String(s.progetto ?? "") !== valore) dopo = {};'),
    ("HZ59", "shared/volta/mods/arturo/volta.js", '        r = await cambiaSessione(s, cosa, valore);', '        r = { ok: true };'),
    ("HZ59", "shared/volta/mods/arturo/volta.js", 'then((l) => apriCambio(s, cosa, progettiNoti(this.dati, l)));', 'then((l) => apriCambio(s, cosa, []));'),
    ("HZ59", "shared/volta/mods/arturo/barra.js", '    else if (c === "volta-cambia") this.volta.cambiaComando(arg, cx);\n', ''),
    ("HZ59", "shared/volta/mods/arturo/main.js", 'macchina: SceltaMacchina, cambio: Cambio, nuovo: Nuovo,', 'macchina: SceltaMacchina, nuovo: Nuovo,'),
    ("HZ59", "shared/volta/mods/arturo/menusessione.js", '      .when(cambi.length > 0, (el) => el.child(gruppo(cambi)))\n', ''),
    ("HZ59", "shared/volta/mods/arturo/menusessione.js", 'const cambi = this.voci.filter((v) => GRUPPI_MENU[1].includes(v.verbo));', 'const cambi = [];'),
    ("HZ59", "shared/volta/mods/arturo/cambio.js", '    run(comandoCambio(this.s, this.cosa, valore));\n    this.chiudi();', '    this.chiudi();\n    run(comandoCambio(this.s, this.cosa, valore));'),
    ("HZ59", "shared/volta/mods/arturo/cambio.js", '    if (this.cosa === "progetto" && !valore) return;\n', ''),
    ("HZ59", "shared/volta/mods/arturo/cambio.js", '    this.input.on("submit", () => this.conferma());\n', ''),
    ("HZ59", "shared/volta/mods/arturo/cambio.js", 'kind: "dialog", width: 480 });', 'kind: "popup", width: 480 });'),
    ("HZ59", "shared/volta/mods/arturo/cambio.js", 'const valore = this.cosa === "nome" ? titolo(this.s) : String(this.s.progetto ?? "");', 'const valore = "";'),
    ("HZ59", "shared/volta/mods/arturo/cambio.js", 'progetto: { titolo: "Sposta in un progetto",', 'progetto: { titolo: "Cambia progetto",'),
    ("HZ59", "shared/volta/mods/arturo/sessioni.js", "    const k = progettoNuovo(chiaveProgetto(p));\n", "    const k = progettoNuovo(p);\n"),
    ("HZ98", "shared/volta/mods/arturo/sessioni.js", "prese.sort((a, b) => a.chiusa - b.chiusa || a.v - b.v || a.i - b.i);", "prese.sort((a, b) => a.v - b.v || a.i - b.i);"),
    ("HZ98", "shared/volta/mods/arturo/sessioni.js", "return c.some((x) => x.startsWith(f)) ? 0 : c.some((x) => x.includes(f)) ? 1 : null;", "return c.some((x) => x.includes(f)) ? 0 : null;"),
    ("HZ98", "shared/volta/mods/arturo/sessioni.js", 'const piano = (x) => String(x ?? "").toLowerCase().normalize("NFD")', 'const piano = (x) => String(x ?? "").toLowerCase().normalize("NFC")'),
    ("HZ98", "shared/volta/mods/arturo/sessioni.js", 'return [...prese.slice(0, quanti - 1).map((x) => x.riga), { tipo: "nuova", testo: String(testo).trim() }];', "return prese.slice(0, quanti).map((x) => x.riga);"),
    ("HZ98", "shared/volta/mods/arturo/sessioni.js", "const v = voto([nome, nomeProgetto(nome), ...alternativi(nome)]);", "const v = voto([nome]);"),
    ("HZ98", "shared/volta/mods/arturo/sessioni.js", "const vive = ss.filter((s) => !chiusa(s)).slice(0, VIVE_SENZA_TESTO)", "const vive = ss.filter((s) => !chiusa(s))"),
    ("HZ98", "shared/volta/mods/arturo/apri.js", "return cerca(this.sessioni, this.lista ?? [], this.filtro);", "return cerca([], this.lista ?? [], this.filtro);"),
    ("HZ99", "shared/volta/keys.json", '"cmd-k": "arturo.apri"', '"cmd-k": "arturo.note"'),
    ("HZ99", "shared/volta/keys-ctrl.json", '"ctrl-shift-a": "arturo.apri"', '"ctrl-shift-a": "arturo.note"'),
    ("HZ67", "shared/volta/mods/arturo/comandi.js", '  if (/^nuova-(?:[0-9a-f]{4})+$/.test(c)) return { verbo: "nuova", arg: dopo("nuova-"), lungo: true };', '  if (c.startsWith("nuova-")) return { verbo: "nuova", arg: dopo("nuova-"), lungo: true };'),
    ("HZ100", "shared/volta/installa-herdr.sh", "if tasti is None:\n", "if False:\n"),
    ("HZ100", "shared/volta/installa-herdr.sh", 'serie=keys-herdr-macos.json\n', 'serie=keys-herdr.json\n'),
    ('HZ101', 'shared/volta/mods/arturo/casa.js', 'comandoConversazione(t.chiave)', 'comandoApri(t.chiave)'),
    ('HZ101', 'shared/volta/mods/arturo/comandi.js', '  if (c.startsWith("conversazione-")) return { verbo: "conversazione", arg: dopo("conversazione-"), lungo: true };\n', ''),
    ('HZ101', 'shared/volta/mods/arturo/sessioni.js', '  if (giroSt?.ultimo && ora - giroSt.quando <= GIRO_MS) return giroSt.ultimo;\n', ''),
    ('HZ101', 'shared/volta/mods/arturo/sessioni.js', '  return li ?? sessioneDi(terminale, sessioni);', '  return sessioneDi(terminale, sessioni) ?? li;'),
    ('HZ102', 'shared/volta/mods/arturo/volta_sposta.py', '    if gi["ramo"] == "HEAD":\n', '    if False:\n'),
    ('HZ102', 'shared/volta/mods/arturo/volta_sposta.py', 'd.update(progetto=a["progetto"], fonte="teletrasporto", quando=time.time())', 'd.update(progetto=a["progetto"], fonte="persona", inizio=False, quando=time.time())'),
    ('HZ102', 'shared/volta/mods/arturo/volta_sposta.py', '    return re.sub(r"[^A-Za-z0-9]", "-", p)', '    return re.sub(r"[^A-Za-z0-9/]", "-", p)'),
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
    if caso == "HZ92" and os.name == "nt":
        return "il claude finto della sonda è uno script sh: su Windows il caso si ferma prima di fasi e frasi"
    if caso in ("HZ63", "HZ78", "HZ79") and os.name == "nt":
        return "il ponte del microfono c'è solo sul Mac: su Windows mancano il microfono virtuale e i segnali"
    if caso in ("HZ13", "HZ16") and not mac:
        return "Arturo.app e i servizi di launchd ci sono solo sul Mac"
    return None


def avvelena(repo: Path) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from salti_windows import dichiara  # noqa: PLC0415
    esiti, saltati = [], 0
    fuori = serve_arturo() if senza_arturo(repo) else set()
    for caso, rel, giusto, rotto, *solo in VELENI:
        if caso in fuori:
            dichiara(f"veleno {caso} ({rel})", "il caso chiede file di Arturo, che qui non ci sono")
            esiti.append(caso)
            saltati += 1
            continue
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
            try:
                rossi = prova(copia, caso)  # solo il caso sorvegliato: tutti i casi per ogni veleno superano i 30 minuti del gate
            finally:
                ferma_nati_in(copia)
            codici = [r.split()[0] for r in rossi]
            if caso not in codici:
                print(f"VELENO {caso} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {caso} ROSSO: {next(r for r in rossi if r.startswith(caso))[:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)} saltati={saltati}")
    return 0 if len(esiti) == len(VELENI) else 1


def ferma_nati_in(cartella: Path) -> int:
    """Ferma i processi lanciati da un file dentro `cartella` (la copia di un veleno), e dice quanti.
    Un veleno che rompe lo spegnimento del ponte (HZ78, HZ79) lascia volta_microfono.py ricevi acceso
    dopo che la copia è sparita: il 12/11/2026 su un Mac erano 8, sull'altro più di 20 (#5423).
    Solo dove c'è ps: su Windows i casi del ponte non lanciano ricevitori veri."""
    if os.name == "nt":
        return 0
    try:
        out = subprocess.run(["ps", "-axo", "pid=,args="], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return 0
    radici = {str(cartella), os.path.realpath(cartella)}
    fermati = 0
    for riga in out.splitlines():
        pid, _, args = riga.strip().partition(" ")
        if pid.isdigit() and int(pid) != os.getpid() and any(r + os.sep in args for r in radici):
            try:
                os.kill(int(pid), 15)
                fermati += 1
            except OSError:
                pass
    return fermati


def veleni_senza_testo(repo: Path) -> list:
    """I veleni che non trovano una volta sola il loro testo da rompere, in pochi secondi e senza lanciarli.
    Il 12/11/2026 undici veleni erano rimasti così dopo le copie del mod: il banco era verde, e solo i 15
    minuti di --avvelena del gate li vedevano (#5468). Il banco di ogni giro, e così pubblica-mod.py, li
    vede subito."""
    rossi = []
    fuori = serve_arturo() if senza_arturo(repo) else set()
    for caso, rel, giusto, *_ in VELENI:
        if caso in fuori:
            continue
        f = repo / rel
        n = f.read_text(encoding="utf-8").count(giusto) if f.is_file() else 0
        if n != 1:
            rossi.append(f"{caso} veleno senza testo da rompere: {giusto[:60]!r} c'è {n} volte in {rel}")
    return rossi


def spazio_volta(repo: Path) -> Path:
    """Dal repository di Volta (c'è arturo/mods/arturo, non shared/volta) il banco gira su una copia di arturo/
    messa come shared/volta/ in una cartella temporanea, tolta all'uscita. Una copia e non un link: i veleni
    e i casi scrivono dentro il mod. Dal repository di Arturo resta il repository com'è."""
    if not (repo / "arturo" / "mods" / "arturo").is_dir() or (repo / "shared" / "volta").is_dir():
        return repo
    import atexit  # noqa: PLC0415
    tmp = Path(tempfile.mkdtemp(prefix="banco-volta-"))
    atexit.register(shutil.rmtree, tmp, True)
    shutil.copytree(repo / "arturo", tmp / "shared" / "volta",
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "cache"))
    return tmp


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    repo = spazio_volta(Path(argomenti.repo).resolve())
    # il registro eventi del mod (#5549) va in una cartella del banco, mai in quello vero della persona
    os.environ["VOLTA_REGISTRO"] = tempfile.mkdtemp(prefix="banco-registro-")
    if argomenti.avvelena:
        return avvelena(repo)
    if argomenti.baseline_ref:
        print("BASELINE_DISCRIMINANTE=nessuna (banco nuovo: il veleno lo prova con --avvelena)")
        return 0
    rossi = prova(repo) + veleni_senza_testo(repo)
    for r in rossi:
        print("ROSSO", r)
    girati = len(CASI) - len(SALTATI)
    print(f"herdr: {girati - len({r.split()[0] for r in rossi})}/{girati} casi verdi"
          + (f", {len(SALTATI)} saltati perché chiedono file di Arturo" if SALTATI else ""))
    return 1 if rossi else 0


if __name__ == "__main__":
    if os.name == "nt" and not sys.flags.utf8_mode:
        # Su Windows text=True e la console sono cp1252: il banco leggerebbe storto l'UTF-8 di node e dei mod,
        # e 8 casi uscivano rossi per le sole accentate (#5166). -X utf8 vale solo per il banco: i figli
        # Python partono come li lancia il prodotto, senza ereditare la modalità.
        raise SystemExit(subprocess.run([sys.executable, "-X", "utf8", *sys.argv]).returncode)
    raise SystemExit(main())
