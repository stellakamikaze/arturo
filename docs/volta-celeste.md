# Volta Celeste, la finestra di Arturo

Volta Celeste è la finestra di Arturo: tiene le sessioni di Claude Code in una finestra sola. Nasce da [Herdr](https://herdr.dev), un'app gratuita e open source (Apache 2.0), e ne resta compatibile: stessi comandi (`herdr-app`, `herdr-core`, `hc`), stessa cartella `~/.config/herdr-app`, stessi mod e layout. Oggi Arturo installa Herdr durante `/setup`, dopo il tuo sì, con un layout suo, e in questa guida "Herdr" nomina l'app installata. Il layout è questo:

- **A sinistra, i tuoi progetti.** Per ognuno una frase: "Claude ti aspetta", "Claude sta lavorando", "3 cose per te", "fermo". In cima quelli che aspettano te. Un clic apre il progetto: se la sessione è chiusa, ne parte una nuova con `/inizio <progetto>`.
- **Al centro, la conversazione con Claude.** Scrivi come in una chat. "Altra conversazione" ne apre una seconda sullo stesso progetto.
- **A destra, Da fare.** I todo del progetto divisi per chi agisce: "Tocca a te", "Decidi tu, poi fa Claude", "Ci pensa Claude", "Fermi". La casella segna un todo fatto. "Lavoraci" segna il todo in corso e porta Claude su quel todo: finché è in corso la riga dice se Claude ci sta lavorando o ti aspetta, e "Vai da Claude" riporta alla sessione. `/fine` lo chiude se il lavoro è finito, altrimenti lo rimette da fare con una nota. "Altro" cambia chi lo fa e quando, lo ferma (con cosa aspetta), aggiunge una nota o lo scarta col motivo. "Aggiungi", in alto, scrive un todo nuovo senza passare da Claude.
- **In basso,** quante sessioni lavorano e quante ti aspettano.
- **La settimana,** in basso a sinistra: i progetti con todo scaduti, quelli che aspettano te e quelli fermi da più di sette giorni, ognuno in una lista sola. "Fai il punto" apre Claude sul progetto con `/inizio`. La finestra si apre da sola alla prima apertura di ogni settimana, se c'è qualcosa da guardare.

**Per cominciare.** Al primo avvio una guida di quattro passi mostra cosa sa fare la finestra; poi resta alla voce "Guida". "Cosa posso chiedere", in basso a sinistra e in alto, raccoglie le richieste da imparare: un clic e Claude parte. Chi non ha ancora progetti vede "Trova i miei progetti": Claude cerca sul computer le cartelle di lavoro con le stesse regole di `/setup` (un sì per ogni lettura, niente file spostati) e crea un progetto per ogni lavoro che confermi ([shared/volta-celeste/trova-progetti.md](../shared/volta-celeste/trova-progetti.md)). Le cartelle della base dei progetti compaiono a sinistra anche senza todo.

**Per chi usa già Arturo.** All'avvio di una sessione, una volta sola, Claude propone la finestra in una riga. Col sì installa Herdr e il layout come in `/setup`.

I todo sono quelli di `arturo todo`: se li tieni in un altro strumento ([fonte dei task](fonte-task.md)), il pannello legge quello.

## Cosa installa e dove

- Herdr, dall'installer ufficiale di herdr.dev, che ne controlla firma e integrità: l'app in `~/Applications` (Mac) o nel menu Start (Windows), e `herdr-core`, il programma che tiene vive le sessioni anche a finestra chiusa, in `~/.local/bin`.
- Il layout di Arturo in `~/.config/herdr-app` (`layouts/arturo.json`, `themes/arturo*.json`, `mods/arturo/`) e `arturo.json`, che dice al pannello dove sono Arturo e i tuoi progetti.
- Un hook di Claude Code, `hooks/herdr-stato.sh`: dice a Herdr se Claude lavora, aspetta te o ha finito. Fuori da Herdr non fa niente.
- Sul Mac, `~/Applications/Arturo.app` e il LaunchAgent `~/Library/LaunchAgents/org.stellakamikaze.arturo-app.plist`, che le rimette nome e icona dopo ogni aggiornamento di Herdr ([più sotto](#il-nome-arturo-nel-dock)).
- Le note che lasci con ⌘⇧N (Ctrl+Shift+M su Windows), in `~/.claude/data/note-finestra/`: restano su questo computer, fuori da git.
- La nascita in background ([più sotto](#le-sessioni-del-terminale-nascono-in-background)): `volta-claude` e `volta-nascita.sh` in `~/.config/herdr-app` (su Windows anche `volta-claude.ps1`) ci sono sempre. Il blocco marcato in `~/.zshrc` o `~/.bashrc`, o nel profilo di PowerShell su Windows, c'è solo se la scegli.

Funziona sui Mac con processore Apple e su Windows. Sui Mac Intel e su Linux `/setup` salta il passo, e Arturo funziona come sempre nel terminale.

## Cosa non è neutro

- **Aggiornamenti.** Herdr si aggiorna da solo da herdr.dev, non dai rilasci firmati di Arturo. Un aggiornamento di Herdr può cambiare il suo aspetto prima che Arturo lo segua.
- **Telemetria.** Herdr manda di suo, una volta al giorno, dei conteggi d'uso: versione, sistema, quanti spazi e terminali, quali agenti, layout e comandi. Mai il contenuto dei terminali né i nomi dei tuoi file. Arturo la spegne all'installazione (`"telemetry": false` in `~/.config/herdr-app/settings.json`): se vuoi aiutare chi fa Herdr, la riaccendi da Impostazioni → Privacy.
- **Tasti.** Arturo aggiunge ⌘O (apri un progetto), ⌘⇧↓ e ⌘⇧↑ (sessione dopo e prima), ⌃⌘→ e ⌃⌘← (progetto dopo e prima), ⌘⇧N (una nota a Claude su un punto della finestra), ⌘⇧E (l'elenco delle note). Su Windows ⌘ sarebbe il tasto Windows, che il sistema si tiene: lì Arturo aggiunge Ctrl+Shift+A (apri un progetto), Ctrl+Shift+M (la nota) e Ctrl+Shift+I (l'elenco delle note), e per sessioni e progetti valgono i tasti di Herdr, Alt+↓ e Alt+↑, Ctrl+Shift+PagGiù e PagSu. Un tasto che usavi già per altro resta tuo.

## Come si toglie

- Il layout: in Herdr ⌃⇧L passa al layout di Herdr; per toglierlo cancella `layouts/arturo.json` e `mods/arturo/` in `~/.config/herdr-app`.
- Herdr: cancella l'app da `~/Applications` e `~/.local/bin/herdr-*`, `~/.local/bin/hc`.
- Arturo.app, sul Mac: prima ferma il LaunchAgent, altrimenti la ricrea, con `launchctl bootout gui/$(id -u)/org.stellakamikaze.arturo-app`; poi cancella `~/Library/LaunchAgents/org.stellakamikaze.arturo-app.plist` e `~/Applications/Arturo.app`.
- La firma locale, se l'hai creata: in Accesso Portachiavi cancella la voce "Arturo firma locale" (certificato e chiave). Senza, Arturo.app torna alla firma ad hoc e macOS richiede i permessi a ogni aggiornamento di Herdr.
- Le note sulla finestra: cancella `~/.claude/data/note-finestra/`. La riga `note_progetto` in `~/.config/herdr-app/arturo.json` dice dove vanno le note: toglierla le manda al progetto aperto.
- La nascita in background: `sh ~/.config/herdr-app/volta-nascita.sh togli` toglie il blocco da `~/.zshrc`, `~/.bashrc` e dai profili di PowerShell, e il resto dei file resta com'era. Vale dalla prossima finestra del terminale. Poi cancella `volta-claude`, `volta-claude.ps1`, `volta-nascita.sh` e `nascita-no` in `~/.config/herdr-app`.
- Per reinstallare o aggiornare il layout: `sh ~/.claude/shared/volta-celeste/installa-herdr.sh`.

## Un altro Mac come macchina di Herdr

Herdr apre terminali anche su un altro computer, aggiunto con `hc machine add` via ssh. Su un Mac, l'`herdr-core` partito da ssh non ha il permesso di macOS per Documenti e Scrivania: un terminale che parte da lì resta vuoto, perché già `path_helper` della shell di login si ferma ad aprire la cartella (provato il 9/11/2026 su un secondo Mac, #5013; da `/tmp` e dalla home passa). Per riattaccare una sessione (`claude attach`) fai partire il terminale dalla home: la sessione resta nella sua cartella. Per lavorare in Documenti da quel Mac, dai a `herdr-core` l'accesso in Impostazioni di Sistema → Privacy e sicurezza → File e cartelle, su quel Mac.

Il login. Su quel Mac il gestore delle sessioni in background (`claude daemon`) e `herdr-core` partono su richiesta, dal primo programma che li cerca. Se il primo arriva da ssh, partono senza il portachiavi, e ogni sessione risponde "Not logged in", anche agganciata da qui. Per `herdr-core` il rimedio è `sh ~/.claude/shared/volta-celeste/servizi-gui.sh`, lanciato su quel Mac dopo `hc server stop`: `herdr-core` riparte dalla sessione grafica (provato il 9/11/2026 su un secondo Mac). Il gestore non va fermato prima: lo script ne accende uno nuovo, che prende il posto di quello acceso e ne riprende le sessioni vive.

### Il servizio di Claude, fisso su ogni macchina

Il gestore delle sessioni in background è il servizio di Claude. Se parte dal primo `claude --bg`, vive a tempo: muore con chi l'ha fatto nascere, e da ssh nasce senza login. Per questo Volta, prima di ogni sessione nuova su qualunque macchina e prima di Riavvia, lancia lì `volta_sonda.py servizio <macchina>`. Lo lancia anche il comando `claude` del terminale con la nascita accesa, su questa macchina, prima di `claude --bg`: costa meno di un secondo se il servizio c'è già. Da ssh il comando non lo lancia, perché lì nascerebbe senza login; se il servizio non parte, lo dice e la sessione nasce lo stesso. Se il servizio risponde, non lo tocca. Se manca, lo accende dove sopravvive:
- sul Mac con il LaunchAgent `org.stellakamikaze.arturo.claude-daemon`, se c'è; senza, staccato in una sessione sua, figlio di `herdr-core` o di Volta, che hanno il login e l'accesso a Documenti. Staccato vale fino al riavvio;
- su Windows con l'attività `ArturoServizioClaude`, se c'è; senza, in un terminale di `herdr-core` (`hc run`), nella sessione grafica.

Il servizio fisso parte da solo a ogni accesso, e l'installazione lo propone con la riga `HERDR SERVIZIO`:
- su Windows `powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\.config\herdr-app\servizio-claude.ps1"` registra l'attività e la avvia, senza finestra (provato il 10/11/2026 sul PC Windows dello studio); con `-Togli` in fondo la toglie. `/setup` la registra col tuo sì;
- sul Mac `servizi-gui.sh --launchd` mette anche il LaunchAgent del servizio. Prima dai a `claude` l'accesso a Documenti (Impostazioni di Sistema, Privacy e sicurezza, File e cartelle): nato da launchd senza quel permesso, il servizio ha il login ma le sessioni in `~/Documents` muoiono all'avvio. Senza `--launchd`, lo script apre il servizio in una finestra del Terminale, che gli passa il suo accesso a Documenti: la finestra va lasciata aperta. `servizi-gui.sh --rimuovi` toglie i due LaunchAgent.

L'attesa. Una sessione nuova aspetta prima le macchine (15 s), poi il servizio (120 s), poi la nascita (180 s): Volta aspetta fino a 6 minuti prima di dire che la macchina non risponde. Riavvia aspetta il servizio (120 s) e il gesto (60 s), fino a 3 minuti e mezzo; gli altri gesti un minuto e mezzo. Il banco HZ41-HZ43 prova il servizio, le attese e i nomi; HZ35 e HZ38 il servizio prima del comando `claude`.

## Tutte le sessioni, di tutte le macchine

In cima alla barra di sinistra la sezione "Tutte le sessioni" elenca le sessioni di Claude Code aperte su ogni macchina, raggruppate per macchina o per progetto (l'interruttore sotto il titolo; la scelta resta). Le macchine sono quelle aggiunte a Herdr (`hc machine ls`): questa per prima, poi le altre, lette con `hc exec --on <macchina>`, Windows compreso. Una macchina senza Claude Code (un server, un Raspberry) resta fuori. Ogni 30 secondi il mod lancia `volta_sonda.py volta --scrivi ~/.cache/volta/sessioni.json`, che sta nella cartella del mod, e rilegge il file. Un altro script si indica in `arturo.json` alla voce `volta`. Una macchina che non risponde, se Volta ci aveva già visto Claude, resta con le sue ultime sessioni note e la nota "Non risponde".

In ogni gruppo stanno prima le sessioni che ti aspettano, poi quelle con un errore, poi quelle al lavoro; le ferme si aprono con "N ferme". Il clic:
- su una sessione in background apre una scheda con `claude attach`, via `ssh -t` se è su un'altra macchina, nello spazio del suo progetto (o nello spazio "Volta" se non ne ha uno); se la scheda c'è già, la porta davanti;
- su una sessione aperta in un Terminale e ferma lancia `~/.claude/scripts/teletrasporto.py porta-volta`, se c'è (senza, dice di aprirla dal suo Terminale), che scrive `/bg` nella sua casella vuota e restituisce il nuovo id, poi la aggancia;
- su una sessione al lavoro, che aspetta una risposta nel suo Terminale o di una macchina giù, non fa niente e dice perché sotto la riga.

Lo stesso clic arriva anche da `herdr-app do arturo.volta-<id>` (id corto di otto caratteri). Le parti: `sessioni.js` (gruppi, frasi e decisione del clic, senza Herdr, provato da HZ17-HZ18 con node) e `volta.js` (letture, sezione); l'aggancio è `aggancia()` di `dati.js`.

**Il titolo di una sessione.** Ogni riga porta poche parole in italiano che dicono il lavoro in corso ("Prova dei gesti sulle sessioni"). Le scrive `hooks/titolo-sessione.py` in `~/.claude/cache/titolo/<sessione>.json`: alla prima richiesta il compito di `/inizio` o la richiesta accorciata, poi a ogni fine turno un modello piccolo (Haiku) le riscrive leggendo le ultime richieste e l'ultima risposta, al massimo ogni 10 minuti per sessione. La sonda le legge su ogni macchina (campo `titolo`), e `titolo()` di `sessioni.js` le mette davanti al nome di Claude Code. Costa una chiamata breve per turno sulla quota della persona; `ARTURO_TITOLI=0` in `env` di `settings.json` la spegne, e allora resta il nome di Claude o la prima riga dell'ultima risposta. Un titolo scritto va a capo su due righe. Senza una scelta della persona l'elenco si apre "Per progetto"; `herdr-app do arturo.volta-gruppi-progetto` (o `-macchina`) sposta l'interruttore (banco HZ45).

"Altro", a destra di una sessione in background, apre i gesti in un riquadro sotto l'elenco, col titolo della sessione e "Chiudi": il riquadro sta fuori dalla parte che scorre, così si vede anche per una sessione in fondo (`pannello()` di `volta.js`, banco HZ47). I gesti: **Anteprima** mostra senza aprirla l'ultima risposta di Claude e la sua ultima azione, a capo nella barra: sono i campi `risposta` e `azione` che la sonda legge già dalla trascrizione, quindi non parte nessun comando e il testo segue le letture dopo (`anteprima()` di `sessioni.js`, banco HZ46). Una risposta oltre i 400 caratteri arriva tagliata a una parola intera, col segno "…". Solo se la trascrizione manca Volta mostra le ultime righe dello schermo (`claude logs`, ridisegnato perché le parole restino spaziate). **Ferma** la ferma se lavora o ti aspetta (la conversazione resta, un clic la riapre), **Riavvia** la fa ripartire dopo un errore, e prima accende il servizio di Claude su quella macchina se manca (vedi "Il servizio di Claude, fisso su ogni macchina"), **Elimina** la cancella se è ferma, dopo un secondo clic su "Sì, elimina". Se Claude Code rifiuta (per esempio commit non pubblicati nel suo worktree), la riga dice perché. I gesti passano da `volta_sonda.py azione <macchina> <logs|stop|respawn|rm> <id>`: qui con `claude`, su un'altra macchina con `hc exec --on`. Quando una sessione di qualunque macchina passa a "ti aspetta", Volta lo avvisa; lo stato di ogni sessione va anche in `arturo.volta.stati`, per le schede che agganciano una sessione in background. Il banco è HZ40. Una sessione fermata o in errore resta nell'elenco fra le ferme: la sonda chiede `claude agents --all` e tiene le chiuse nate negli ultimi tre giorni (`CHIUSE_GIORNI` in `volta_sonda.py`). Per le prove, senza clic: `herdr-app do arturo.volta-altro-<id>` apre e chiude "Altro", `herdr-app do arturo.volta-gesto-<logs|stop|respawn|rm>-<id>` preme un suo bottone (per Elimina due volte: la seconda conferma); banco HZ44.

### Una sessione nuova su un'altra macchina

Sotto "Nuova richiesta" e "Apri un progetto" della barra, sotto "Nuova richiesta" del benvenuto e in cima alla finestra "Apri un progetto", la riga "Nasce su" sceglie dove nasce la sessione: questa macchina o una delle altre con Claude Code che Volta elenca. La scelta resta; da tastiera è `herdr-app do arturo.dove-<macchina>` (`dove-qui` per questa). Su un'altra macchina la sessione nasce in background con `volta_sonda.py nasci <macchina> [--progetto <slug>] [-- <prompt>]`: via `hc exec --on`, nella cartella dei progetti di quella macchina (`base` del suo `arturo.json`, perché `claude --bg` vuole una cartella fidata), col progetto scritto per Volta. Poi si aggancia qui in una scheda, nello spazio del progetto o in "Volta". Chiudere la scheda non la ferma, e Volta la apre da ogni macchina (provato il 10/11/2026 da un Mac su un PC Windows). Se non nasce, un avviso dice perché: macchina spenta, Claude assente, cartella non fidata. Seguono "Nasce su" anche il clic su un progetto, "Lavoraci" e "Fai il punto", quando il progetto non ha ancora uno spazio; con lo spazio di una sessione nata altrove, "Lavoraci" scrive nella sua scheda. Le richieste di "Cosa posso chiedere" restano su questa macchina, perché parlano dei suoi progetti, dei suoi todo e della sua configurazione. Su questa macchina la sessione resta interattiva nel terminale di Herdr: agganciata con `claude attach` perde lo stato nella barra, finché Volta non lo legge dall'elenco delle sessioni. Provato da HZ39.

## Le sessioni del Terminale nascono in background

Volta apre da un'altra macchina solo le sessioni in background: una sessione aperta col comando `claude` nel Terminale è legata a quella finestra. Con la nascita in background il comando `claude` la fa nascere in background (`claude --bg`) e la apre subito lì con `claude attach`. Prima di `claude --bg` il comando accende il servizio di Claude se manca (`volta_sonda.py servizio qui`), tranne da ssh: il motivo sta in "Il servizio di Claude, fisso su ogni macchina". Sul Mac lancia la sonda con `python3`; su Windows col Python che l'installazione ha scritto in `arturo.json`, perché lì `python3` può essere il segnaposto dello Store. Nel Terminale lavori come prima, e Volta la apre da ogni macchina anche mentre lavora, senza spostarla né fermarla. Due finestre sulla stessa sessione vedono lo stesso lavoro allo stesso momento (provato il 10/11/2026). Chiudere il Terminale non ferma la sessione: `claude attach <id>` la riapre, e Volta la elenca.

La propone l'installazione (`HERDR NASCITA`), e `/setup` la accende col tuo sì: `sh ~/.config/herdr-app/volta-nascita.sh metti`. Col no, `/setup` lancia `sh ~/.config/herdr-app/volta-nascita.sh no`, che lo ricorda: l'installazione non la ripropone, e `metti` la accende quando vuoi. Sul Mac il blocco va in `~/.zshrc` (o `~/.bashrc`) e fa passare il comando `claude` da `~/.config/herdr-app/volta-claude`. Su Windows va nel profilo di PowerShell (`$PROFILE`, sia di Windows PowerShell sia di PowerShell 7) e lo fa passare da `volta-claude.ps1`; lì la via di fuga è `$env:CLAUDE_QUI = 1`, poi `claude`. `sh ~/.config/herdr-app/volta-nascita.sh stato` dice dove è acceso.

Restano come prima, interattive nel terminale:
- `CLAUDE_QUI=1 claude`, la via di fuga;
- i sottocomandi (`claude agents`, `attach`, `mcp`, `logs`, ...), `-p`, `--version`, `--continue` e `--resume` senza id (con l'id va in background);
- `claude` lanciato da uno script, senza un terminale, o da dentro una sessione di Claude;
- i terminali di Herdr: lì lo stato della sessione (lavora, aspetta) arriva dall'hook nel terminale, e una sessione in background non ce l'ha. Passano in background quando Volta leggerà lo stato dall'elenco delle sessioni.

Se `claude --bg` rifiuta la cartella, la sessione si apre qui come prima e lo dice. Succede in una cartella che Claude Code non ha ancora segnato come fidata (lancia `claude` lì una volta e accetta), e nella home, che Claude Code fida a una sessione alla volta.

Due cose da sapere:
- una sessione in background prende l'ambiente dal servizio di Claude Code (`claude daemon`), non dalla shell che la lancia: una variabile esportata solo in quel Terminale non arriva. Per quella sessione usa `CLAUDE_QUI=1`;
- se hai già una funzione `claude` (in `~/.zshenv`, `~/.zshrc`, `~/.bashrc` o nel profilo di PowerShell), vince la tua e l'installazione lo dice (`HERDR NASCITA FUNZIONE`). Per avere la nascita in background, falla finire con `"$HOME/.config/herdr-app/volta-claude" "$@"` al posto di `command claude "$@"`, o in PowerShell con `& "$HOME\.config\herdr-app\volta-claude.ps1" @args`;
- su Windows PowerShell legge il profilo solo se la sua ExecutionPolicy lo permette: con `Restricted`, il valore di partenza di Windows PowerShell, il blocco non parte e l'installazione lo dice (`HERDR NASCITA POLICY`). La policy è un'impostazione di sicurezza tua: se scegli di cambiarla, `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Un profilo salvato in UTF-16 (succede con `>` in Windows PowerShell) resta com'è (`HERDR NASCITA UTF16`).

## Nota del ramo di prova `herdr` (8/11/2026)

Questo è un ramo di prova, fuori dai rilasci. Prima di un rilascio mancano:
- il server della telemetria con `herdr-stato.sh` in `DERIVA_HOOK`, pubblicato prima del tag;
- su Windows, la prova dell'hook dello stato su ConPTY (layout, barra, tasti e sessioni di tutte le macchine provati sul PC Windows dello studio il 9/11/2026);
- l'avviso di Herdr quando una sessione aspetta, oggi in inglese ("Claude Code needs you");
- la voce in `NOVITA.md`, come per ogni altro cambio (`docs/manutenzione.md`).

## Il nome Arturo nel Dock

Sul Mac l'installazione crea `~/Applications/Arturo.app` accanto a `Herdr.app` (`shared/volta-celeste/arturo-app.sh`): la stessa app, col nome, l'identificativo `org.stellakamikaze.arturo` e l'icona di Arturo, firmata in locale. Herdr si aggiorna da sé anche dentro Arturo.app e sostituisce il pacchetto intero, quindi dopo un aggiornamento l'app si chiamerebbe di nuovo Herdr: il LaunchAgent `org.stellakamikaze.arturo-app` guarda i due `Info.plist` e rilancia lo script, che riparte dalla copia più nuova. Con la firma ad hoc macOS lega i permessi (Documenti, microfono, automazione) a una firma che cambia a ogni aggiornamento, quindi li richiede. `shared/volta-celeste/firma-locale.sh`, che l'installazione propone con la riga `HERDR FIRMA` e che la persona lancia nel suo Terminale, crea l'identità "Arturo firma locale" nel portachiavi e la segna come affidabile per la firma del codice (macOS chiede due volte la password del Mac): da lì Arturo.app tiene la stessa identità e i permessi restano.

## Le note sulla finestra (⌘⇧N)

Una nota è un appunto per Claude legato a un punto della finestra: "questo bottone è storto", "qui vorrei la data". È il modo di lavorare di Agentation, rifatto per una finestra che non è una pagina web.

**Lasciare una nota.** Premi ⌘⇧N (Ctrl+Shift+M su Windows): la finestra si vela. Clicca il punto di cui vuoi parlare, scegli il tipo (Correggere, Cambiare, Domanda, Va bene così) e scrivi. Invio la manda, Esc annulla. La nota prende un numero, e Claude la trova fra le sue cose da fare di oggi nel progetto aperto, oppure in quello scritto in `note_progetto` di `arturo.json` nella cartella di Herdr. Senza un progetto la nota resta salvata, ma non arriva fra le cose da fare.

**Vedere le note.** Col velo aperto le note ancora da chiudere compaiono come segni numerati nel loro punto: arancioni se aspettano, grigi se Claude ci sta lavorando. Fuori dal velo i segni non si vedono, perché Herdr non ha un velo che lasci passare i clic ai terminali. La barra di stato in basso dice quante note sono aperte: il conteggio, o ⌘⇧E (Ctrl+Shift+I su Windows), apre l'elenco, con "Aperte" e "Tutte" per vedere anche le chiuse.

**Rispondere e chiudere.** Un clic su un segno, o su una riga dell'elenco, apre la nota con le risposte. Da lì scrivi a Claude (Rispondi), la dai per fatta (Risolta) o la togli col motivo (Scarta). Quando Claude risponde, la finestra lo avvisa: "Claude ha risposto alla nota N". Chiudere la nota chiude anche la cosa da fare collegata, da qualunque parte la chiudi.

**Dove stanno.** Ogni nota ha una cartella in `~/.claude/data/note-finestra/<data-ora>/` con `nota.json`, lo scatto della finestra fatto prima del velo (`finestra.png`) e, dopo che Claude l'ha aperta, il ritaglio attorno al punto (`ritaglio.png`). La cartella è fuori da git. Se il punto cade su un terminale, la nota tiene anche il terminale, la cartella in cui lavora e le sue ultime righe.

**Per Claude**: le note si leggono e si chiudono con `arturo note`. Il giro è elenco, mostra, prendi, lavoro, risolvi:

- `arturo note elenco` dà le note aperte coi numeri dei segni; `--md` le scrive come un brief, `--tutte` aggiunge le chiuse, `--progetto P` tiene un solo progetto, `--json` le dà come dati.
- `arturo note mostra ID` dà la nota intera (tipo, parte della finestra, terminale, filo) e scrive `ritaglio.png` attorno al punto, in scala sullo scatto: con ffmpeg il punto ha un quadrato arancione, senza ritaglia sips, e senza nessuno dei due vale lo scatto intero.
- `arturo note prendi ID` dice a chi l'ha scritta che ci lavori: il segno diventa grigio e la cosa da fare passa in corso.
- `arturo note rispondi ID "testo"` scrive nel filo: la finestra avvisa "Claude ha risposto alla nota N".
- `arturo note risolvi ID "cosa hai fatto"` e `arturo note scarta ID "perché"` chiudono la nota e la cosa da fare collegata.

ID è il nome della cartella della nota, oppure il suo numero se fra le note aperte un solo segno lo porta. Se la finestra scrive sulla nota nello stesso momento, il comando rilegge e rifà la sua modifica: nessuna risposta si perde.

Prendi, rispondi, risolvi e scarta hanno due opzioni. `--chi` dice chi scrive: `claude`, il predefinito, oppure `federico`, cioè la persona che ha lasciato la nota; i bottoni della finestra passano da qui con `--chi federico`, e così risolvi e scarta vanno anche senza testo. `--json` stampa la nota dopo il gesto, con `todo_esito` che dice cosa è successo alla cosa da fare collegata. Un testo che comincia con due trattini va dopo `--`.
