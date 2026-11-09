# Herdr, la finestra di Arturo

[Herdr](https://herdr.dev) è un'app gratuita e open source (Apache 2.0) che tiene le sessioni di Claude Code in una finestra sola. Arturo la installa durante `/setup`, dopo il tuo sì, con un layout suo:

- **A sinistra, i tuoi progetti.** Per ognuno una frase: "Claude ti aspetta", "Claude sta lavorando", "3 cose per te", "fermo". In cima quelli che aspettano te. Un clic apre il progetto: se la sessione è chiusa, ne parte una nuova con `/inizio <progetto>`.
- **Al centro, la conversazione con Claude.** Scrivi come in una chat. "Altra conversazione" ne apre una seconda sullo stesso progetto.
- **A destra, Da fare.** I todo del progetto divisi per chi agisce: "Tocca a te", "Decidi tu, poi fa Claude", "Ci pensa Claude", "Fermi". La casella segna un todo fatto. "Lavoraci" segna il todo in corso e porta Claude su quel todo: finché è in corso la riga dice se Claude ci sta lavorando o ti aspetta, e "Vai da Claude" riporta alla sessione. `/fine` lo chiude se il lavoro è finito, altrimenti lo rimette da fare con una nota. "Altro" cambia chi lo fa e quando, lo ferma (con cosa aspetta), aggiunge una nota o lo scarta col motivo. "Aggiungi", in alto, scrive un todo nuovo senza passare da Claude.
- **In basso,** quante sessioni lavorano e quante ti aspettano.
- **La settimana,** in basso a sinistra: i progetti con todo scaduti, quelli che aspettano te e quelli fermi da più di sette giorni, ognuno in una lista sola. "Fai il punto" apre Claude sul progetto con `/inizio`. La finestra si apre da sola alla prima apertura di ogni settimana, se c'è qualcosa da guardare.

**Per cominciare.** Al primo avvio una guida di quattro passi mostra cosa sa fare la finestra; poi resta alla voce "Guida". "Cosa posso chiedere", in basso a sinistra e in alto, raccoglie le richieste da imparare: un clic e Claude parte. Chi non ha ancora progetti vede "Trova i miei progetti": Claude cerca sul computer le cartelle di lavoro con le stesse regole di `/setup` (un sì per ogni lettura, niente file spostati) e crea un progetto per ogni lavoro che confermi ([shared/herdr/trova-progetti.md](../shared/herdr/trova-progetti.md)). Le cartelle della base dei progetti compaiono a sinistra anche senza todo.

**Per chi usa già Arturo.** All'avvio di una sessione, una volta sola, Claude propone Herdr in una riga. Col sì lo installa come in `/setup`.

I todo sono quelli di `arturo todo`: se li tieni in un altro strumento ([fonte dei task](fonte-task.md)), il pannello legge quello.

## Cosa installa e dove

- Herdr, dall'installer ufficiale di herdr.dev, che ne controlla firma e integrità: l'app in `~/Applications` (Mac) o nel menu Start (Windows), e `herdr-core`, il programma che tiene vive le sessioni anche a finestra chiusa, in `~/.local/bin`.
- Il layout di Arturo in `~/.config/herdr-app` (`layouts/arturo.json`, `themes/arturo*.json`, `mods/arturo/`) e `arturo.json`, che dice al pannello dove sono Arturo e i tuoi progetti.
- Un hook di Claude Code, `hooks/herdr-stato.sh`: dice a Herdr se Claude lavora, aspetta te o ha finito. Fuori da Herdr non fa niente.
- Sul Mac, `~/Applications/Arturo.app` e il LaunchAgent `~/Library/LaunchAgents/org.stellakamikaze.arturo-app.plist`, che le rimette nome e icona dopo ogni aggiornamento di Herdr ([più sotto](#il-nome-arturo-nel-dock)).
- Le note che lasci con ⌘⇧N, in `~/.claude/data/note-finestra/`: restano su questo computer, fuori da git.

Funziona sui Mac con processore Apple e su Windows. Sui Mac Intel e su Linux `/setup` salta il passo, e Arturo funziona come sempre nel terminale.

## Cosa non è neutro

- **Aggiornamenti.** Herdr si aggiorna da solo da herdr.dev, non dai rilasci firmati di Arturo. Un aggiornamento di Herdr può cambiare il suo aspetto prima che Arturo lo segua.
- **Telemetria.** Herdr manda di suo, una volta al giorno, dei conteggi d'uso: versione, sistema, quanti spazi e terminali, quali agenti, layout e comandi. Mai il contenuto dei terminali né i nomi dei tuoi file. Arturo la spegne all'installazione (`"telemetry": false` in `~/.config/herdr-app/settings.json`): se vuoi aiutare chi fa Herdr, la riaccendi da Impostazioni → Privacy.
- **Tasti.** Arturo aggiunge ⌘O (apri un progetto), ⌘⇧↓ e ⌘⇧↑ (sessione dopo e prima), ⌃⌘→ e ⌃⌘← (progetto dopo e prima), ⌘⇧N (una nota a Claude su un punto della finestra). Un tasto che usavi già per altro resta tuo.

## Come si toglie

- Il layout: in Herdr ⌃⇧L passa al layout di Herdr; per toglierlo cancella `layouts/arturo.json` e `mods/arturo/` in `~/.config/herdr-app`.
- Herdr: cancella l'app da `~/Applications` e `~/.local/bin/herdr-*`, `~/.local/bin/hc`.
- Arturo.app, sul Mac: prima ferma il LaunchAgent, altrimenti la ricrea, con `launchctl bootout gui/$(id -u)/org.stellakamikaze.arturo-app`; poi cancella `~/Library/LaunchAgents/org.stellakamikaze.arturo-app.plist` e `~/Applications/Arturo.app`.
- La firma locale, se l'hai creata: in Accesso Portachiavi cancella la voce "Arturo firma locale" (certificato e chiave). Senza, Arturo.app torna alla firma ad hoc e macOS richiede i permessi a ogni aggiornamento di Herdr.
- Le note sulla finestra: cancella `~/.claude/data/note-finestra/`. La riga `note_progetto` in `~/.config/herdr-app/arturo.json` dice dove vanno le note: toglierla le manda al progetto aperto.
- Per reinstallare o aggiornare il layout: `sh ~/.claude/shared/herdr/installa-herdr.sh`.

## Un altro Mac come macchina di Herdr

Herdr apre terminali anche su un altro computer, aggiunto con `hc machine add` via ssh. Su un Mac, l'`herdr-core` partito da ssh non ha il permesso di macOS per Documenti e Scrivania: un terminale che parte da lì resta vuoto, perché già `path_helper` della shell di login si ferma ad aprire la cartella (provato il 9/11/2026 sul Mac mini, #5013; da `/tmp` e dalla home passa). Per riattaccare una sessione (`claude attach`) fai partire il terminale dalla home: la sessione resta nella sua cartella. Per lavorare in Documenti da quel Mac, dai a `herdr-core` l'accesso in Impostazioni di Sistema → Privacy e sicurezza → File e cartelle, su quel Mac.

## Nota del ramo di prova `herdr` (8/11/2026)

Questo è un ramo di prova, fuori dai rilasci. Prima di un rilascio mancano:
- il server della telemetria con `herdr-stato.sh` in `DERIVA_HOOK`, pubblicato prima del tag;
- la prova su Windows (Git Bash come shell dei terminali di Herdr, l'hook su ConPTY);
- l'avviso di Herdr quando una sessione aspetta, oggi in inglese ("Claude Code needs you").

## Il nome Arturo nel Dock

Sul Mac l'installazione crea `~/Applications/Arturo.app` accanto a `Herdr.app` (`shared/herdr/arturo-app.sh`): la stessa app, col nome, l'identificativo `org.stellakamikaze.arturo` e l'icona di Arturo, firmata in locale. Herdr si aggiorna da sé anche dentro Arturo.app e sostituisce il pacchetto intero, quindi dopo un aggiornamento l'app si chiamerebbe di nuovo Herdr: il LaunchAgent `org.stellakamikaze.arturo-app` guarda i due `Info.plist` e rilancia lo script, che riparte dalla copia più nuova. Con la firma ad hoc macOS lega i permessi (Documenti, microfono, automazione) a una firma che cambia a ogni aggiornamento, quindi li richiede. `shared/herdr/firma-locale.sh`, che l'installazione propone con la riga `HERDR FIRMA` e che la persona lancia nel suo Terminale, crea l'identità "Arturo firma locale" nel portachiavi e la segna come affidabile per la firma del codice (macOS chiede la password): da lì Arturo.app tiene la stessa identità e i permessi restano.

## Le note sulla finestra (⌘⇧N)

Premi ⌘⇧N, clicchi il punto di cui vuoi parlare e scrivi la nota: Claude la riceve fra le sue cose da fare di oggi, nel progetto scritto in `note_progetto` di `arturo.json` della cartella di Herdr, oppure in quello aperto. Lo screenshot si fa prima che il velo compaia. Ogni nota ha una cartella in `~/.claude/data/note-finestra/<data-ora>/` con `nota.json` e `finestra.png`, e la cosa da fare porta nelle note il punto e il percorso.

**Per Claude**: in `nota.json` il punto e la finestra sono in punti dello schermo; lo screenshot è in pixel reali, e il rapporto è la larghezza del PNG divisa `finestra.larghezza`. Per guardare il punto ritaglia il PNG intorno a `punto` moltiplicato per quel rapporto (`ffmpeg -vf crop`), poi lavora e chiudi la cosa da fare.
