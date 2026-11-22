# Installa Arturo con Claude Code

Questa è la copia di riferimento dei passi di installazione. La pagina https://arturo.stellakamikaze.org/inizia/ ne è una copia: se le due dicono cose diverse, vale questa.

## Per te

Hai incollato questo link in Claude Code: adesso Claude installa Arturo per te. Prima di ogni passo che cambia qualcosa, ti chiede il permesso. Per fermarlo premi Esc.

Il tuo accesso, le tue conversazioni, CLAUDE.md e i tuoi plugin restano come sono. In settings.json Claude Code accende solo il plugin. Permessi, regole di blocco e barra in basso li aggiunge /setup, col tuo sì.

Su Mac può aprirsi una finestra di Apple: clicca "Installa". Su Windows possono comparire più conferme: clicca "Sì" a ognuna. Alla fine scrivi `/exit`, poi `claude`, poi `/setup`.

## Per Claude Code

La persona ti ha chiesto di installare Arturo, un progetto open source con licenza MIT: https://github.com/stellakamikaze/arturo. Procedi un passo alla volta e copia i comandi esattamente come sono scritti, senza aggiungerne altri. Se il riassunto di questa pagina non contiene i comandi esatti, scaricala con `curl -fsSL https://raw.githubusercontent.com/stellakamikaze/arturo/landing-v2/INIZIA.md` e leggi il testo completo.

1. Se la persona ti ha incollato solo il link, chiedile: "Vuoi che installi Arturo?". Se non risponde di sì, fermati.
2. Spiega alla persona in tre righe cosa stai per fare.
3. Solo su Windows: se `bash --version`, `python --version` o `node --version` non stampa un numero di versione, chiedi il permesso e lancia:

   ```
   winget install --id Git.Git -e --source winget; winget install --id Python.Python.3.12 -e --source winget; winget install --id OpenJS.NodeJS.LTS -e --source winget
   ```

   Se winget risponde che un programma c'è già, va bene così. Poi chiedi alla persona di chiudere PowerShell, aprire una finestra nuova, scrivere `claude` e incollare di nuovo questo link.
4. Scarica lo script in un file provvisorio e confrontalo con la copia su GitHub:

   ```
   curl -fsSL https://arturo.stellakamikaze.org/installa.sh -o "$HOME/.arturo-installa.da-verificare"
   ```

   ```
   curl -fsSL https://raw.githubusercontent.com/stellakamikaze/arturo/landing-v2/sito/installa.sh | cmp - "$HOME/.arturo-installa.da-verificare" && mv "$HOME/.arturo-installa.da-verificare" "$HOME/.arturo-installa.sh" && echo UGUALE || rm -f "$HOME/.arturo-installa.da-verificare"
   ```

   Se non compare UGUALE, aspetta 5 minuti (GitHub si aggiorna in ritardo) e rilancia i due comandi, una volta sola. Se ancora non compare, fermati e avvisa la persona. Se compare, leggi lo script e riassumilo alla persona in cinque righe.
5. Chiedi il permesso, poi lancia:

   ```
   bash "$HOME/.arturo-installa.sh"
   ```

   Se un permesso di Claude Code blocca il comando, accetta il blocco e non cercare altre strade. Se vuole, la persona può lanciarlo lei scrivendo qui:

   ```
   ! bash ~/.arturo-installa.sh
   ```
6. Se lo script scrive "possibile compromissione", fermati e avvisa la persona. Se scrive righe che cominciano con `MANCA`, segui quelle righe: per ognuna chiedi il permesso e lancia il comando indicato. Se la riga dice di aspettare, aspetta in background. Se chiede di riaprire Claude Code, dillo alla persona e fermati. Altrimenti rilancia il comando del passo 5.
7. Quando lo script scrive "Arturo installato", non lanciare altri comandi. Riporta alla persona, parola per parola, le istruzioni dopo "Adesso".

## Cosa non fare

- Non usare sudo e non chiedere la password di amministratore.
- Non cambiare i permessi di Claude Code e non aggiungere eccezioni.
- Non spostare né cancellare `~/.claude`.
- Non leggere password, chiavi o file .env. Durante l'installazione non aprire le cartelle della persona: sarà /setup a chiederle il permesso.
- Non mandare niente a nessuno.

## Dopo

/setup ti chiede il permesso di leggere le tue conversazioni passate con Claude Code, poi ti chiede di incollare le istruzioni dei tuoi Progetti di claude.ai. Con un secondo permesso guarda i nomi dei file e l'inizio di pochi documenti nelle tue cartelle di lavoro. Non apre mai cartelle di sistema, cartelle nascoste, .ssh, chiavi, password manager, file .env e credenziali. Di Download legge solo i nomi.

Quello che legge passa da Anthropic, come ogni messaggio che scrivi a Claude. Non arriva a chi mantiene Arturo e non finisce nella telemetria. Prima di leggere, Claude te lo dice: "Quello che leggo resta nella cronologia di questa conversazione, che Claude Code tiene sul tuo computer e cancella da sola dopo 90 giorni. Arturo non ne fa altre copie." Il tuo CLAUDE.md lo approvi tu prima che venga salvato. Cosa raccoglie la telemetria: https://arturo.stellakamikaze.org/privacy/

Progetto di Federico Nejrotti.
