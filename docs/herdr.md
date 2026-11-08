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

Funziona sui Mac con processore Apple e su Windows. Sui Mac Intel e su Linux `/setup` salta il passo, e Arturo funziona come sempre nel terminale.

## Cosa non è neutro

- **Aggiornamenti.** Herdr si aggiorna da solo da herdr.dev, non dai rilasci firmati di Arturo. Un aggiornamento di Herdr può cambiare il suo aspetto prima che Arturo lo segua.
- **Telemetria.** Herdr manda di suo, una volta al giorno, dei conteggi d'uso: versione, sistema, quanti spazi e terminali, quali agenti, layout e comandi. Mai il contenuto dei terminali né i nomi dei tuoi file. Arturo la spegne all'installazione (`"telemetry": false` in `~/.config/herdr-app/settings.json`): se vuoi aiutare chi fa Herdr, la riaccendi da Impostazioni → Privacy.
- **Tasti.** Arturo aggiunge ⌘O (apri un progetto), ⌘⇧↓ e ⌘⇧↑ (sessione dopo e prima), ⌃⌘→ e ⌃⌘← (progetto dopo e prima). Un tasto che usavi già per altro resta tuo.

## Come si toglie

- Il layout: in Herdr ⌃⇧L passa al layout di Herdr; per toglierlo cancella `layouts/arturo.json` e `mods/arturo/` in `~/.config/herdr-app`.
- Herdr: cancella l'app da `~/Applications` e `~/.local/bin/herdr-*`, `~/.local/bin/hc`.
- Per reinstallare o aggiornare il layout: `sh ~/.claude/shared/herdr/installa-herdr.sh`.

## Nota del ramo di prova `herdr` (8/11/2026)

Questo è un ramo di prova, fuori dai rilasci. Prima di un rilascio mancano:
- il server della telemetria con `herdr-stato.sh` in `DERIVA_HOOK`, pubblicato prima del tag;
- un invito, una volta sola dall'avvio, per chi ha già Arturo e non ripassa da `/setup`;
- la prova su Windows (Git Bash come shell dei terminali di Herdr, l'hook su ConPTY);
- l'avviso di Herdr quando una sessione aspetta, oggi in inglese ("Claude Code needs you").
