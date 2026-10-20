# Novità

Questo file è il canale di aggiornamento di Arturo. Ogni volta che l'harness evolve in un
modo che vale la pena raccontare, qui compare una entry: cosa cambia, il principio dietro,
a chi serve. La entry più recente sta in cima, con data ISO nell'intestazione.

Non serve leggerlo a mano: dopo un `git pull`, all'avvio della sessione Arturo ti avvisa se
c'è qualcosa che non hai ancora visto, e `/novita` te lo racconta in parole semplici —
con la possibilità di fare sparring (`/sparring`) per capire se la novità serve al tuo
modo di lavorare.

---

## 2026-10-20 — Arturo lavora come chi lo mantiene: /inizio, /fine e lo stile Conciso

**Cosa cambia**: `/inizio` ti mostra il lavoro per filone, con chi deve agire («Faccio io»,
«Preparo io, poi tu», «Decidi tu»), e rispondi a parole invece che da un menu. Con `-- compito`
Claude ti mostra prima come ha capito la richiesta. Se un'altra sessione lavora sullo stesso
progetto, `/inizio` se ne accorge e lavora in una copia separata. `/fine` non corregge più niente
all'ultimo momento: un test rosso o un pezzo mancante diventa un todo, e il lavoro fatto in una
copia separata torna nel progetto. Lo stile di partenza è Conciso: risposte brevi, prima l'esito.
Lo stile Guida e l'agente doc-reviewer escono.

**Il principio dietro**: chi mantiene Arturo usa ogni giorno questi comandi. Se i tuoi fossero
diversi, i loro difetti resterebbero invisibili a chi può correggerli.

**Da sapere**: se avevi scelto lo stile Guida, dalla prossima sessione vale quello standard di
Claude Code. Per tornare a uno stile breve scrivi `/output-style` e scegli Conciso.

---

## 2026-10-20 — La memoria è la stessa di chi mantiene Arturo

**Cosa cambia**: la memoria facoltativa di Arturo ora è Melchior, la memoria che chi mantiene
Arturo usa ogni giorno: lo stesso codice, copiato identico. Le tue note restano dove sono e come
sono: quelle che Claude Code scrive da solo, le cartelle che hai aggiunto, e una cartella nuova,
`~/.claude/data/memory/`, per le note che curi tu (fuori da git, come i todo). Il richiamo trova
anche due note con lo stesso nome in due progetti, e non conta due volte una nota raggiunta da due
posti. All'avvio, se c'è, Claude riceve la scheda del progetto in cui lavori. Il controllo sulle
note che Claude scrive guarda anche gli URL che portano dati fuori, e fida gli host che hai messo
in `hooks/hosts-interni.local`. La memoria resta spenta finché non la accendi.

**Il principio dietro**: chi mantiene Arturo deve usare quello che usi tu. Con due memorie diverse,
i difetti della tua restano invisibili a chi la mantiene. Le sue note invece non arrivano a te:
nel repository c'è solo il codice.

**Da sapere**: niente da fare. `arturo memoria stato` dice dove cerca e quante note trova, e
`arturo memoria accendi` la accende. Se ci sono parole che il richiamo deve ignorare, scrivile una
per riga in `hooks/melchior-stopword.local`.

---

## 2026-10-20 — Meno domande inutili, meno uscite nascoste, e l'installazione non ti fa perdere niente

**Cosa cambia**: Claude ti chiede conferma meno spesso dove non serve. Copiare una cartella con
`--exclude .env` o cancellare una cartella temporanea appena creata non chiedono più niente.
Chiedono invece alcuni modi nascosti di mandare dati fuori, che prima passavano: un comando dentro
lo user-agent o il referer di `curl`, un `curl` dentro un `echo`, `requests` in Python. Lo stesso per alcune
forme di `git clean` e di cancellazione di cartelle da Python che prima sfuggivano. Chi installa
Arturo su un Claude Code già usato non perde più login, sessioni passate, cronologia e plugin: dopo
il download tornano al loro posto. `/diagnosi` controlla anche l'installazione di Claude Code e i
test dei mod, e la guida spiega `claude --safe-mode`. Nel Terminale di macOS l'avvio non chiede più
il permesso di Automazione per il titolo della finestra.

**Il principio dietro**: una domanda inutile insegna a rispondere sì senza leggere. Le guardie
devono fermarsi dove c'è un rischio vero e tacere altrove. E un'installazione non deve costarti il
lavoro che avevi già.

**Da sapere**: niente da fare. Se un aggiornamento non si installa da solo, adesso chi mantiene
Arturo vede il motivo (un'altra sessione aperta, la firma, la versione) e può correggerlo.
Con Chrome aperto e l'estensione Claude in Chrome attiva, l'aggiornamento automatico non partiva
mai: Arturo scambiava il ponte con Chrome per una sessione aperta. Ora lo riconosce. E se un'altra
sessione aperta rimanda davvero l'aggiornamento, l'avvio dopo te lo dice, con il modo di
installarlo subito.

---

## 2026-10-19 — Se manca node, la barra in basso te lo dice

**Cosa cambia**: la barra in basso mostra il modello, quanto contesto hai usato e la quota del tuo
abbonamento. È uno script che gira con node. Claude Code oggi si installa anche senza node, e su un
computer appena preparato la barra restava vuota senza dire perché. Ora, se node manca, la barra
scrive «Arturo: manca node» e l'avvio della sessione lo dice a Claude, che ti aiuta a installarlo.
Lo stesso vale per l'avviso che ti dice quando il contesto sta per finire.

**Il principio dietro**: uno strumento che si spegne in silenzio sembra funzionare. Se qualcosa
non può partire, Arturo lo dice nel punto dove lo stai cercando.

**Da sapere**: node si scarica da nodejs.org (l'installer per Mac è un file .pkg). Dopo
l'installazione chiudi e riapri Claude Code. Se la barra resta vuota anche con node, dillo con
`/segnala`.

---

## 2026-10-19 — Claude Code torna con tutte le sue funzioni, e le guardie vedono anche Monitor

**Cosa cambia**: Arturo non spegne più la telemetria di Claude Code. Quando era spenta, Claude Code
smetteva anche di scaricare le impostazioni delle sue funzioni, e ne perdevi alcune senza saperlo.
Tra queste c'è il segno sui testi incollati, che aiuta Claude a non scambiare per tue le istruzioni
scritte da altri. Le altre sono l'esclusione dei collegamenti rotti che bloccavano ogni richiesta,
la compattazione della conversazione mentre sei via e `/skill-doctor`, che dice quali skill non usi.
Con le funzioni accese arriva anche Monitor, lo strumento con cui Claude segue un comando in
background: le guardie ora controllano anche i suoi comandi. In più una guardia che non riesce a
partire ferma l'azione invece di lasciarla passare.

**Il principio dietro**: Arturo non deve togliere a chi lo usa le difese che Claude Code ha già.
Spegnere la telemetria di Claude Code era una scelta presa all'inizio e mai spiegata, e costava più
di quanto proteggeva. Secondo Anthropic quegli eventi non contengono codice, percorsi dei file o
comandi. Una guardia che si rompe in silenzio è peggio di una guardia che ti ferma per sbaglio.

**Da sapere**: se vuoi la telemetria di Claude Code spenta lo stesso, "Cosa non è neutro" nel
README spiega come e cosa perdi. Su Windows lo strumento PowerShell resta spento, perché le guardie
di Arturo controllano solo Git Bash. Con Claude Code più vecchio della 2.1.300 `/setup` ti chiede di
aggiornarlo.

---

## 2026-10-19 — Conferma per le ricerche che eseguono programmi, e Sonnet di riserva

**Cosa cambia**: tre comandi di ricerca e lettura (`rg`, `sed -n` e `find`) non sono più approvati
in blocco. Quando cercano o leggono, passano senza domanda come prima. Quando eseguono un programma
o riscrivono un file, Claude ti chiede conferma. Due esempi: `rg --pre`, che passa ogni file a un
programma, e `sed -n -i`, che modifica il file sul posto. Prima passavano senza domanda. In più, se
il modello principale è sovraccarico, Claude continua con Sonnet invece di fermarsi con un errore.

**Il principio dietro**: una regola che approva un comando intero approva anche le sue forme
pericolose. Claude Code riconosce già da solo le forme che leggono e basta, quindi la regola larga
aggiungeva solo il rischio. Un errore di sovraccarico, per chi inizia, sembra un guasto: con un
modello di riserva il lavoro va avanti.

**Da sapere**: niente da fare.

---

## 2026-10-19 — La scheda del terminale anche sul Mac, e niente falsi rossi da igiene e iTerm2

**Cosa cambia**: sul Mac la scheda del terminale ora cambia davvero titolo e colore: prima restava
ferma. Nel Terminale di Apple, che non colora le schede, il titolo comincia con "● TOCCA A TE" quando
Claude aspetta te, e la scheda in secondo piano mostra la campanella. Il controllo di igiene su
GitHub gira solo sul repository pubblico di Arturo. Se salvi la tua `~/.claude` in un repository
privato, non ricevi più l'email "Run failed: igiene" a ogni `/fine`. E se un programma aggiunge a
`settings.json` hook suoi senza `matcher` (lo fa iTerm2 con `cc-status`), l'avvio non dice più
"una guardia potrebbe non proteggere".

**Il principio dietro**: con più sessioni aperte devi vedere da fuori quale ti aspetta, senza
entrare in ogni scheda. E un avviso falso insegna a ignorare quelli veri. Il controllo di igiene cerca
i nomi dell'autore di Arturo, e nei tuoi appunti non ha niente da cercare. Un hook senza `matcher` è
lecito per Claude Code, e le guardie di Arturo restavano al loro posto.

**Da sapere**: niente da fare. Le correzioni su igiene e iTerm2 vengono dalle vostre segnalazioni con `/segnala`.

---

## 2026-10-17 — Solo rilasci firmati, anche con /aggiorna, e guardie che vedono di più

**Cosa cambia**: `/aggiorna` installa solo l'ultimo rilascio firmato da chi mantiene Arturo, come
l'aggiornamento automatico, e mai le modifiche pubblicate dopo. Se l'ultimo rilascio non ha una firma
valida, l'avvio, la barra in basso, `/inizio` e `/novita` dicono "possibile compromissione: non
aggiornare, segnala a chi mantiene Arturo", e `/aggiorna` non installa niente, neanche col tuo sì. In
più Claude ti chiede conferma prima di: leggere un file `.env` (dove stanno le chiavi dei servizi),
cancellare una cartella con `shutil.rmtree` o i file non salvati in git con `git clean -f`, allineare
una cartella con `rsync --delete`, mandare dati fuori con un `curl` che costruisce l'indirizzo con un
comando, una pipe verso `nc` o il codice di `node` e `python` che chiama la rete.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer. Prima la firma
proteggeva solo l'aggiornamento automatico: proprio quando un rilascio non era firmato, l'avviso ti
mandava a `/aggiorna`, che lo installava lo stesso. Una firma che manca è il segno che qualcosa non
va, e la risposta giusta è fermarsi e dirlo. Le guardie nuove seguono la regola di sempre: chiedono
dove un errore non si annulla, e restano zitte sul lavoro normale. Un `curl` qualsiasi, un `rsync`
senza `--delete`, `git clean -n` e la cartella `build/` passano senza domande.

**Da sapere**: niente da fare. Se vedi "possibile compromissione", non cercare un'altra strada per
aggiornare: segnalalo con `/segnala`, o in privato come dice `SECURITY.md`. Per controllare la firma
servono git 2.34 e OpenSSH 8.2, o più recenti: con versioni più vecchie Arturo non si aggiorna e lo
dice, senza parlare di compromissione.

Corretto anche un guasto segnalato da chi usa Arturo: se avevi aggiunto righe a
`hooks/session-start.sh` o `session-end.sh`, `/aggiorna` diceva di averle spostate in
`~/.claude/personale/`, ma il file non arrivava e le righe si perdevano. Ora arrivano, commentate come
sempre. Se dopo un aggiornamento ti manca qualcosa all'avvio, chiedi a Claude di ritrovarlo nella
versione di prima: `/aggiorna indietro` sa qual è.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

---

## 2026-10-16 — Arturo si aggiorna da solo, come Claude Code

**Cosa cambia**: non serve più `/aggiorna`. Quando esce una versione nuova, la barra in basso di
Claude Code te lo dice ("↑ Arturo … · si installa alla chiusura"). Quando chiudi la sessione, Arturo
la installa da solo, con la stessa procedura di `/aggiorna`: le tue aggiunte restano tue, e se
qualcosa non torna non cambia niente. Se hai più sessioni aperte, la installa l'ultima che chiudi.
Alla sessione dopo Claude ti dice a che versione sei arrivato, e `/novita` ti racconta cosa cambia.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer. Per questo
si installano da soli solo i rilasci firmati con la chiave di chi mantiene Arturo, e la firma si
controlla con la chiave che hai già: un repository manomesso non basta. Se la firma manca, o la
storia pubblicata è stata riscritta, Arturo non installa niente e te lo dice.

**Da sapere**: preferisci leggere ogni aggiornamento prima? Scrivi a Claude "tieni gli
aggiornamenti a mano", oppure lancia `python3 ~/.claude/bin/arturo aggiornamenti manuali`: resta
l'avviso, e aggiorni con `/aggiorna` come prima. Questa è l'ultima volta che serve `/aggiorna` per
ricevere una versione: da qui in poi arrivano da sole. La telemetria conta a parte gli
aggiornamenti installati da soli (l'esito `automatico` dell'evento `aggiorna`): per questo
all'avvio Claude ti ripete una volta cosa esce.

---

## 2026-10-16 — L'avvio e la chiusura personali non bloccano più gli aggiornamenti

**Cosa cambia**: se hai aggiunto righe all'avvio o alla chiusura della sessione
(`hooks/session-start.sh`, `hooks/session-end.sh`), ogni aggiornamento di Arturo che toccava quei
file andava in conflitto e si fermava. Adesso `/aggiorna` sposta le tue righe in un file tuo,
`~/.claude/personale/session-start.sh` (o `session-end.sh`), che l'hook di Arturo esegue alla fine e
che nessun aggiornamento tocca. Le righe arrivano commentate: Claude le rilegge con te e toglie il
`#` a quelle che devono girare. Se invece hai modificato una delle guardie di sicurezza, l'avvio
adesso te lo dice a parte. Claude ti mostra cosa cambia e, se vuoi, la rimette com'è in Arturo con
`arturo personale ripristina`. Al server di Arturo il riepilogo del lunedì dice anche quante
installazioni nuove non hanno mai lanciato `/setup`.

**Il principio dietro**: le tue aggiunte restano tue senza fermare gli aggiornamenti. Una guardia
allentata è una tua scelta, ma la fai sapendolo. Sono le prime correzioni nate dal ciclo del
lunedì, che legge la telemetria e propone a chi mantiene Arturo cosa sistemare.

**Da sapere**: niente da fare. Se avevi modificato l'avvio, al prossimo `/aggiorna` Claude ti
propone di rileggere le righe spostate.

---

## 2026-10-16 — Le tue skill restano tue, e /setup ti riconosce

**Cosa cambia**: quando `/fine` salva la config verso il tuo repository, le skill nuove che hai
creato con `/creaskill` partono solo se il repository è privato. Se non risulta privato, restano
su questo computer e Claude ti chiede se pubblicarle: una skill tua può contenere dati tuoi.
`/diagnosi` ti dice anche quando un tuo file in `personale/` appartiene a un comando che Arturo
non ha più, come `/strato`: nessuno lo legge, e puoi tenerlo da parte o cancellarlo. Se avevi
finito `/setup` prima di oggi e lo rilanci, Arturo ti riconosce e ti propone la verifica invece
della prima configurazione. Su Windows la telemetria registra anche le conferme dei comandi con
caratteri speciali, e un `rm -rf` nella cartella temporanea di Windows non chiede più conferma,
come `/tmp` sul Mac.

**Il principio dietro**: niente di tuo esce senza un tuo sì, e niente ti fa rifare un lavoro già
fatto.

**Da sapere**: niente da fare.

---

## 2026-10-16 — Su Windows le guardie leggono tutto il comando

**Cosa cambia**: su Windows alcune guardie di Arturo leggevano male i comandi con caratteri
speciali, e in quei casi lasciavano passare senza chiedere. Un `rm -rf` su una cartella con una
virgoletta tipografica («”») nel comando passava senza conferma. Un invio di email con una
freccia ("→") partiva senza conferma. Adesso ogni guardia legge il comando intero, con gli
accenti e i simboli, e ti chiede conferma come sul Mac. Su Windows è corretto anche `/fine`:
un file già salvato in un repository, in una sottocartella, non risulta più da scartare. Lo
scratchpad di Claude adesso conta come cartella temporanea. La memoria trova anche le note
con parole accentate.

**Il principio dietro**: una guardia che si confonde deve chiedere, non tacere. E una correzione
vale solo se un controllo la prova anche sul sistema dove il guasto è nato.

**Da sapere**: niente da fare. Sul Mac non cambia niente. Se provi Arturo in una cartella
temporanea, da lì la telemetria non parte più verso il server di Arturo: parte solo verso un
server che indichi tu con `ARTURO_TELEMETRIA_URL`.

---

## 2026-10-16 — La scheda del terminale dice il progetto e lo stato

**Cosa cambia**: il titolo della scheda in cui gira Claude Code ora dice su quale progetto lavora.
In Windows Terminal e in iTerm2 il colore della scheda dice lo stato: verde quando Claude aspetta
te, giallo mentre lavora, rosso quando il turno si è fermato per un errore, come un'API giù o un
limite raggiunto. Negli altri terminali lo stato è scritto nel titolo, per esempio "romanzo · al
lavoro". Il progetto è quello scelto con `/inizio`, altrimenti il repository o la cartella
in cui hai aperto Claude Code. Il titolo automatico di Claude Code, quello col riassunto della
conversazione, non c'è più: al suo posto c'è il progetto.

**Il principio dietro**: con tante schede aperte, guardare deve bastare a sapere dove serve una
tua risposta.

**A chi serve**: a chi tiene aperte più sessioni insieme.

---

## 2026-10-16 — Nove comandi, una diagnosi del progetto, e le tue skill con /creaskill

**Cosa cambia**: Arturo ti racconta e ti propone nove comandi: `/inizio`, `/fine`, `/aggiorna`,
`/novita`, `/segnala`, `/setup`, `/guidami`, `/diagnosi` e il nuovo `/creaskill`. Tutto il resto
lo usa Claude da solo, dentro questi: lo sparring, la scrittura semplificata, il brief, i todo,
l'audit. `/setup` adesso fa anche la verifica di una configurazione già fatta: scrivi
`/setup verifica`. `/diagnosi` non guarda più solo il codice ma il progetto intero: controlla
che Arturo regga, lo stato di git, handoff e todo, i file citati negli handoff che non esistono
più, e i materiali sparsi in Download o fuori dal repo, con un posto proposto per ognuno.
`/creaskill` ti fa quattro domande e trasforma un lavoro che fai spesso in una skill tua.

Escono cinque comandi: `/strato` (lo strato delle organizzazioni torna più avanti, rifatto),
il percorso a tappe con `/percorso` e `arturo percorso`, `/progetto`, `/discovery` e
`/write-plan`. Un progetto nuovo lo crei con `/inizio <nome>`: se non esiste, Claude ti chiede
se crearlo.

**Il principio dietro**: pochi comandi che si raccontano bene valgono più di tanti che si
dimenticano. Un comando che nessuno lancia è un comando che nessuno mantiene.

**Da sapere**: se hai aggiornato con `/aggiorna`, i file tolti spariscono da soli. Se avevi
modificato uno dei comandi tolti, `/aggiorna` te lo chiede. Se copi le cartelle a mano, cancella
tu `commands/strato.md`, `commands/progetto.md`, `commands/discovery.md`,
`commands/write-plan.md`, la cartella `skills/percorso/`, `bin/percorso.py`, `docs/esercizi.md`,
`docs/referente.md` e la cartella `templates/`. Il file `session-env/percorso.json` non serve
più e si può cancellare. Se nei tuoi todo c'è il progetto `_percorso`, sono gli esercizi del
percorso: chiedi a Claude di scartarli. Se avevi installato lo strato di un'organizzazione,
resta installato ma non si aggiorna più da solo: `claude plugin list` lo mostra, e
`claude plugin uninstall` lo toglie.

---

## 2026-10-16 — In vista solo i comandi di ogni giorno, Impeccable dal setup, esce blast-radius

**Cosa cambia**: Claude ti propone di sua iniziativa solo i comandi che servono ogni giorno o quando serve:
`/inizio`, `/fine`, `/aggiorna`, `/novita`, `/segnala`, `/setup`. Gli altri (`/guidami`, `/sparring`,
`/progetto`, `/discovery`, `/write-plan`, `/diagnosi`, `/strato`, `/percorso`, `/italiano-semplificato`)
restano tutti: li lanci tu scrivendo il nome. Il README li divide in "Ogni giorno", "Quando serve" e
"Gli altri comandi". In più `/setup` ti propone Impeccable (fase 8c), la skill di design delle
interfacce di Paul Bakaus: la installa dall'autore, con le sue versioni nuove. Esce il mod
`blast-radius`: fermava ogni `rm -rf` e aspettava una risposta, e quando la risposta non arrivava
bloccava anche il lavoro utile scritto nello stesso comando.

**Il principio dietro**: chi comincia ha bisogno di due comandi, non di quindici. Un elenco lungo
fa sembrare difficile anche quello che è semplice. E una guardia che ferma il lavoro più spesso di
quanto lo protegga va tolta.

**Da sapere**: niente da fare. Prima di cancellare una cartella Claude ti chiede ancora conferma
(`block-dangerous`), e il push forzato resta vietato. "A che punto sono?" non apre più da solo il percorso: scrivi `/percorso`.
Se fai siti o pagine e vuoi Impeccable senza rifare tutto il setup: `/setup` e salta alla fase 8c,
oppure leggi `docs/impeccable.md`.

---

## 2026-10-15 — Gmail, Calendar e Drive senza Google Cloud, e guardie con gli accenti

**Cosa cambia**: per collegare la posta, il calendario e i documenti non serve più creare un
progetto su Google Cloud. `/inizio gws` ti propone prima i connettori di claude.ai: li attivi dal
browser, riapri Claude Code e ci sono. La strada vecchia resta per chi usa più account Google. In
più i messaggi delle guardie scrivono "c'è" e "già" con gli accenti veri, non con l'apostrofo.

**Il principio dietro**: il primo collegamento deve stare nei cinque minuti. Se costa un'ora di
pagine in inglese, chi comincia si ferma lì.

**A chi serve**: a chi non ha ancora collegato Google. Scrivi `/inizio gws` dopo il prossimo
`/aggiorna`.

---

## 2026-10-15 — Guardie che non perdono il filo, e il brief su ogni richiesta

**Cosa cambia**: una review di Arturo ha trovato comandi che la shell esegue e che le guardie non
vedevano: un `<<` scritto dentro virgolette, un delimitatore come `'E'OF`, un testo mandato a
`/bin/bash` o scritto in un file e poi eseguito. Ora una guardia toglie il testo di un heredoc solo
quando i confini sono certi e il testo va a un lettore come `cat`: nel dubbio lo controlla. In
modalità auto il controllo di sicurezza di Claude Code tiene anche le sue regole di serie, `gh` è
libero solo in lettura (un `gh gist create --public` passa dal giudizio) e una lettura di
`~/.claude/data/credentials/` chiede conferma. Il brief torna su ogni richiesta di lavoro, anche
breve: per una richiesta piccola bastano tre righe.

**Il principio dietro**: il testo che una guardia toglie è testo che non controlla. Meglio una
domanda in più che un comando che passa senza essere visto.

**A chi serve**: a tutti, senza fare niente: arriva col prossimo `/aggiorna`.

---

## 2026-10-15 — Le tue modifiche ai comandi si mettono da parte da sole

**Cosa cambia**: se hai modificato un comando di Arturo (per esempio hai aggiunto a `/inizio` la
tabella dei tuoi progetti) e l'aggiornamento cambia lo stesso comando, `/aggiorna` sposta da solo le
tue righe in un file tuo, `~/.claude/personale/inizio.md`. Il comando torna quello di Arturo e non
va più in conflitto. Quando lanci `/inizio`, Claude legge anche le tue righe, quindi il comando fa
tutto quello che faceva prima. Non devi fare niente: Claude te lo dice in una frase. Lo spostamento
avviene nella copia di prova: se l'aggiornamento non va in porto, la tua config non cambia. Se hai un
tuo repository della config, deve essere privato: solo così `personale/` viaggia fra le tue macchine.
Se non lo è, le tue modifiche restano dove sono, come prima.

**Il principio dietro**: la tua config e quella di Arturo convivono senza che tu debba pensarci.
Le tue modifiche restano tue, gli aggiornamenti cambiano solo i file di Arturo.

**A chi serve**: a chi ha già cambiato un comando di Arturo. Gli altri non vedono differenze.

---

## 2026-10-15 — Un solo modo di leggere gli heredoc per tutte le guardie

**Cosa cambia**: quattro guardie leggevano gli heredoc ognuna a modo suo, e sbagliavano in punti
diversi. Una here-string (`<<<"x"`) faceva sparire il resto del comando: una lettura di
`~/.ssh` scritta dopo passava senza conferma. Il testo mandato a bash con `cat <<'EOF' | bash`
sfuggiva a due guardie su quattro. Ora le quattro usano lo stesso modulo, `hooks/heredoc.py`.

**Il principio dietro**: il testo che una guardia toglie è testo che non controlla. Quattro copie
della stessa regola divergono, e il buco sta sempre nella copia che nessuno ha guardato.

**A chi serve**: a tutti, senza fare niente: arriva col prossimo `/aggiorna`.

---

## 2026-10-15 — Guardie che leggono il comando come lo esegue la shell

**Cosa cambia**: un invio di email o messaggi da terminale ora chiede conferma invece di essere
bloccato: vedi il comando vero e decidi tu. Le guardie leggono il comando come lo esegue la shell:
il testo di un heredoc scritto su file, un messaggio di commit e il pattern di `grep` non fanno più
scattare allarmi, mentre un `rm` col percorso completo o dentro `sh -c` si vede. Un git hook o un
servizio che parte all'accesso (`~/Library/LaunchAgents` su Mac, `~/.config/systemd/user` e
`~/.config/autostart` su Linux) si scrive solo con la tua conferma. Le reti locali contano tutte
come interne (anche `172.16.x`-`172.31.x` e le IPv6 locali); un servizio esterno che usi con la tua
chiave lo scrivi in `hooks/api-fidate.local`. Salvare un handoff o una memoria non chiede più
conferma; settings, hook e file di sblocco la chiedono sempre. La statusline mostra il ramo git, un
`*` se ci sono modifiche e la quota dell'abbonamento. Dopo ogni modifica a un file TypeScript o Vue
Claude vede subito gli errori di tipo. Creare una bozza via un collegamento non chiede conferma,
inviarla sì.

**Il principio dietro**: un blocco che sbaglia insegna a Claude ad aggirare la guardia, una
conferma mostra a te il comando vero. Queste correzioni girano da settimane nella config
dell'autore.

**Da sapere**: all'avvio Arturo prova le sue guardie in background, al massimo ogni 12 ore, senza
rallentare la sessione. Se una guardia non funziona su questo computer, la sessione dopo una riga
`GUARDIE` te lo dice. Li spegni con `ARTURO_BANCHI_AVVIO=0`. Se il tuo `CLAUDE.md` supera le 200
righe, Claude ti avvisa quando lo modifica (il limite si cambia con `ARTURO_CLAUDE_MD_RIGHE`).

## 2026-10-15 — Gate che non mentono, lavori lunghi, lettura del web senza browser

**Cosa cambia**: il gate di `/fine` è uno script (`bin/validation-gate-lang.sh`). Riconosce se il
progetto è Node, Python o testo, e lancia i controlli giusti. Prima il gate leggeva l'esito dei test
in un modo che, nella shell di Claude Code, poteva restare vuoto e sembrare un verde. Un comando lungo
ha una strada sua, `bin/bgjob.sh`: gira staccato dalla sessione e scrive l'esito su un file.
`/system-audit` segnala anche i comandi citati nei documenti che non esistono più, e i plugin
installati ma spenti. In `/setup` c'è una fase facoltativa per `scrape`, che legge una pagina web e
tiene solo il testo utile.

**Il principio dietro**: un controllo vale solo se sa dire "rosso". Ogni gate nuovo ha un caso
avvelenato, una versione rotta apposta che deve bocciare. Il "non so" è un esito onesto: il testo e
gli strumenti mancanti danno "inconclusivo", mai verde.

**Da sapere**: `scrape` occupa circa 300 MB e si installa solo se dici sì in `/setup`. Non finge di
essere un browser: se un sito blocca i programmi, te lo dice e ti consiglia di aprire la pagina nel
browser. La pulizia mensile (`bin/monthly-cleanup.sh`) è facoltativa: prova prima con `--prova`.

## 2026-10-15 — /inizio e /fine: il contesto in una chiamata, un handoff che regge

**Cosa cambia**: `/inizio` raccoglie il contesto del progetto in una chiamata sola
(`arturo contesto`): cosa è cambiato in git, la ripartenza degli ultimi handoff, i todo aperti
divisi fra te e Claude, le scadenze dei prossimi giorni e il todo da cui ripartire. Con
`/inizio --tutti` aggiorna anche tutti i progetti della tua cartella dei progetti. `/fine` parte
dall'inventario dei file che la sessione ha scritto, anche fuori dal progetto (Download, Scrivania,
cartelle temporanee), e propone dove deve finire ognuno. Prima di chiudere controlla l'handoff: la
tabella dei pendenti c'è sempre, ogni riga è un todo vero dell'archivio, e chi agisce è tu, decidi
o io. Tiene gli ultimi 5 handoff per progetto, ma prima ti mostra cosa conteneva quello che esce, e
rigenera l'indice dei progetti.

**Il principio dietro**: una sessione nuova vale quanto quello che trova. Un handoff che dice "cosa
resta" senza dire cosa, o un file lasciato in una cartella che sparisce al riavvio, è lavoro perso.
Meglio un controllo che ferma la chiusura che una ripartenza al buio.

**Da sapere**: gli handoff restano solo sul tuo computer, come prima, e viaggiano fra le tue
macchine solo se la config ha un remote privato. I file che l'inventario trova fuori da un progetto
non si spostano da soli: Claude ti chiede dove li tieni. Da terminale il contesto lo vedi con
`python3 ~/.claude/bin/arturo contesto <progetto>`.

## 2026-10-15 — /apri, avvisi sotto il prompt, esempi per lo strato

**Cosa cambia**: scrivi `/apri` e si apre l'ultimo link o file che Claude ha citato, con il
programma predefinito del tuo computer. Sotto il prompt, oltre alla cache fredda, compaiono due
avvisi nuovi: i banchi delle guardie sono rossi, oppure un account Google della CLI `gws` va
ricollegato. Se usi `gws`, un errore di credenziali ora si dichiara al primo colpo, con il comando
per rifare il login. La skill dell'italiano semplificato ha un catalogo dei tic della scrittura
generata. Chi cura lo strato di un'organizzazione trova in `esempi/` tre modelli da adattare: le
email che imparano dalle correzioni, il recap delle riunioni dalla trascrizione intera, l'anteprima
prima dell'invio. Per il design delle interfacce, `docs/impeccable.md` spiega come installare
Impeccable dall'autore.

**Il principio dietro**: un avviso compare solo quando c'è qualcosa da fare. Una cosa che esiste già
fatta bene altrove si installa da lì, non si copia.

**Da sapere**: gli esempi dello strato non sono attivi finché il referente non li copia nello
strato. L'avviso dei banchi compare solo se un banco è rosso: i banchi partono da soli
all'avvio, al massimo ogni 12 ore, e il rimedio è lo stesso della riga `GUARDIE`. L'avviso di `gws`
tace se non usi `gws`. Per spegnere un mod: `/plugin`, poi il mod, poi disattiva.

## 2026-10-15 — Una memoria che puoi accendere

**Cosa cambia**: Claude Code salva da solo alcune note sulle sessioni passate: cosa preferisci,
cosa hai deciso, dove stanno le cose. Ora Arturo può usarle in ogni progetto. Se accendi la
memoria, a ogni messaggio Arturo cerca le note che parlano della stessa cosa e dice a Claude dove
sono. Claude le apre solo se servono. Ogni nota e ogni handoff che Claude scrive passa da un
controllo, anche a memoria spenta: se dentro c'è una password o un'istruzione nascosta, Claude riceve un avviso. Con
`arturo memoria cerca "parole"` cerchi a mano, con `arturo memoria controlla` trovi le note senza
descrizione e i link rotti. Puoi aggiungere una tua cartella di note con
`arturo memoria cartella aggiungi <cartella>`.

**Il principio dietro**: una memoria serve se la trovi quando ti serve, e se non porta dentro
niente che non hai scritto tu. Le note restano tue e restano qui: nessun server, nessun archivio
nuovo, niente nella telemetria.

**Da sapere**: la memoria è spenta. Si accende in `/setup` oppure con
`python3 ~/.claude/bin/arturo memoria accendi`, e si spegne con `arturo memoria spegni`. Spegnerla
non cancella nessuna nota. `arturo memoria` da solo ti dice se è accesa e quante note vede.

## 2026-10-15 — La telemetria si allarga, e serve a correggere Arturo ogni settimana

**Cosa cambia**: la telemetria di Arturo manda qualche evento in più, sempre senza contenuti. Partono
la fase di `/setup` a cui arrivi, il nome di una guardia che ti chiede conferma e se poi hai detto sì,
una guardia che si rompe, un `/aggiorna` rifiutato, annullato o scartato, la versione di Claude Code,
e del percorso a tappe i soli numeri: la tappa, quante decisioni e limiti hai tenuto, quante proposte
di delega e quanti no. Mai cosa hai scritto. Alla prima sessione dopo l'aggiornamento Claude ti dice
di nuovo cosa esce, perché la promessa è cambiata. L'elenco intero è nell'Impegno 3 del README.

**Il principio dietro**: chi comincia spesso non sa dire dove si blocca. Ogni lunedì chi mantiene
Arturo legge dove le persone si fermano: una fase di `/setup` abbandonata, una guardia che chiede e
riceve sempre sì (una domanda inutile insegna a rispondere sì senza leggere), un aggiornamento che
nessuno vuole, una tappa dove si resta fermi. Da lì nascono le correzioni, e ognuna lo dirà nella sua
voce di questo file. Sono numeri, non verdetti: il giudizio resta a una persona.

**Da sapere**: la spegni quando vuoi con `python3 ~/.claude/bin/arturo telemetria spegni`, e
`python3 ~/.claude/bin/arturo telemetria mostra` ti fa vedere esattamente cosa parte. L'id che parte
con gli eventi è casuale ma resta lo stesso: per questo non li chiamiamo anonimi.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-15 — Scegli come ti scrive Claude

**Cosa cambia**: Arturo porta due stili di scrittura. **Guida**, lo stile di partenza, scrive frasi
semplici, senza gergo, e dice prima l'esito e poi cosa devi fare tu. **Conciso** è per chi usa Claude
ogni giorno e vuole leggere poco. `/setup` ha una fase nuova per scegliere fra questi due e i tre
di Claude Code (Default, Explanatory, Learning). Lo cambi quando vuoi con `/output-style`.

**Il principio dietro**: lo stile standard di Claude Code è scritto per chi sviluppa software. Chi
usa Claude per scrivere, cercare e ordinare il lavoro merita risposte pensate per lui.

**Da sapere**: dopo questo aggiornamento le risposte arrivano nello stile Guida, dalla sessione
successiva. Lo stile cambia solo la scrittura: permessi e guardie restano gli stessi. Se vuoi uno
stile tuo, crealo in `~/.claude/output-styles/` con un nome nuovo: nessun aggiornamento lo tocca.

## 2026-10-15 — Guardie più strette dove servono, meno allarmi dove non servono

**Cosa cambia**: Claude chiede conferma prima di leggere una password con `bw get`, di aprire un
file `.env`, di rispondere, inoltrare o condividere via un collegamento (Gmail, Calendar, Drive,
GitHub) e di correggere un commit con `--amend`. Non può più eseguire codice arbitrario nel browser
né lanciare un altro Claude senza permessi. Il controllo dei segreti nei commit parte anche con le
forme che prima lo saltavano (`env … git commit`, un commit a capo, `git --no-pager commit`). Un
indirizzo `.ts.net` non conta più come interno: se lavori con la tua tailnet, scrivi i tuoi host in
`hooks/hosts-interni.local`. Due falsi allarmi spariscono: `sed` in lettura seguito da un ciclo
`for w`, e `rsync --delete` in prova (`-n`) o citato in un testo. La statusline torna a mostrare il
task in corso, e il suono parte solo quando Claude aspetta te.

**Il principio dietro**: una guardia vale se ferma il danno vero e tace sul lavoro normale. Queste
correzioni arrivano dalla config dell'autore, dove giravano da settimane.

**Da sapere**: se usavi `bw get` senza conferma, ora Claude te la chiede ogni volta. È voluto: la
password finirebbe nella conversazione. Gli allow larghi (`python3`, `curl`, `docker`, `brew`)
escono: nella modalità auto decide il controllo di sicurezza di Claude Code, che ora riceve
istruzioni chiare su cosa è lavoro normale (script di prova, pulizia dei rami già uniti, commit nei
tuoi repository). I comandi di sola lettura (`ls`, `cat`, `git status`…) restano liberi.

## 2026-10-14 — Arturo convive con la tua config

**Cosa cambia**: le tue aggiunte a un comando di Arturo hanno un posto loro,
`~/.claude/personale/<comando>.md`. Quando lanci il comando Claude le legge, e nessun aggiornamento
le tocca. Se hai già modificato un comando di Arturo, `/aggiorna personale` sposta le tue modifiche
lì e riporta il comando com'era: l'aggiornamento successivo non va più in conflitto. All'avvio una
riga `DERIVA` ti avvisa quando la distanza da Arturo rischia di rompere qualcosa: un comando
modificato, un hook di Arturo tolto o spento. Il promemoria del brief non scatta più sui comandi e
sulle richieste chiare e piccole: solo su un lavoro che tocca più file, ha effetti fuori dal
computer o si può capire in due modi.

**Il principio dietro**: Arturo accompagna la tua config, non la sostituisce, e non deve intralciare
l'uso naturale dell'LLM. Dove le due config si toccano serve un confine chiaro: il tuo da una parte,
quello di Arturo dall'altra.

**Da sapere**: la telemetria ha due eventi nuovi, `deriva` e `config`. Dei file esce solo la
posizione dentro Arturo, che è pubblica: mai i tuoi file né i percorsi del tuo computer. Una config
rotta parte subito, perché spegne le guardie. La spegni come sempre con
`python3 ~/.claude/bin/arturo telemetria spegni`.

## 2026-10-14 — Prima di cancellare vedi cosa sparisce, e zsh si comporta come bash

**Cosa cambia**: un mod nuovo, `blast-radius`. Quando Claude sta per lanciare `rm -rf`, `git reset
--hard`, `git clean` o un push forzato, il comando si ferma e compare un pannello: quanti file
spariscono e quali, quali modifiche non salvate si perdono, quali commit. Premi Procedi o Annulla.
`riscrivi-bash` fa comportare zsh, la shell del Mac, come bash: un glob che non trova file
(`ls *.png` in una cartella senza png) non ferma più il comando con "no matches found". Escono due
mod che nessuno usava: `menu-contesto` e `agent-flow`.

**Il principio dietro**: prima di un gesto che non si annulla, devi vedere cosa fa, non leggere
un comando. E una comodità che nessuno apre è solo codice da mantenere.

**Da sapere**: niente da fare. Se `blast-radius` ti ferma troppo spesso, spegnilo con `/plugin`.


## 2026-10-14 — Una striscia per i conti, e il controllo degli invii guarda cosa gira davvero

**Cosa cambia**: sotto la frase che riassume i tuoi todo, la pagina di `arturo web` ha una
striscia. Ogni pezzo è largo quanto la sua parte: quelli che toccano a te, quelli da decidere,
quelli in mano a Claude, quelli fermi. A colpo d'occhio vedi dove pesa il lavoro. Il controllo
degli invii email ora giudica il comando che gira, non le parole che contiene: cercare "smtplib"
in una cartella o scriverlo in una nota non si ferma più. Si fermano invece forme che prima
passavano: `find -exec sendmail`, `awk` con `system()`, `git send-email`, un testo mandato a `sh`.

**Il principio dietro**: una guardia che blocca la prosa insegna ad aggirarla. Una guardia che
lascia passare un invio travestito non protegge. Si giudica il codice eseguito.

**Da sapere**: niente da fare. Se hai uno script tuo che usa `git send-email`, ora Claude ti chiede
conferma prima di lanciarlo.

## 2026-10-13 — Meno dati in uscita, copie di prova che non si perdono, guardie più precise

**Cosa cambia**: quattro correzioni. La telemetria manda il nome di un comando solo se il comando è
di Arturo: un comando che hai scritto tu in `~/.claude/commands/` ha un nome tuo, e da oggi non parte.
Se un aggiornamento o il sync fra le tue macchine si è fermato su un conflitto, la copia di prova
con il conflitto resta finché non la concludi o dici di scartarla: prima un `/aggiorna` successivo la
toglieva in silenzio, con il lavoro che c'era dentro. All'avvio della sessione Arturo te la ricorda.
`/segnala` torna al canale diretto anche se con la prima versione avevi usato la email o il web.
`/strato` funziona dal secondo passo in poi, e `pubblica` non manda niente se un controllo fallisce.

**Il principio dietro**: una promessa vale per quello che il codice fa, non per quello che il README
dice. La telemetria prometteva "il nome di un comando di Arturo", e mandava il nome di qualunque
comando. Lo stesso vale per le guardie: un invio verso fuori non deve passare solo perché nello
stesso comando compare anche un indirizzo interno.

**Da sapere**: scrivere un `CLAUDE.md` da terminale (`>`, `sed -i`, `cp`) ora chiede conferma, come
già succedeva modificandolo con Claude. Leggerlo o copiarlo altrove no. Il controllo delle emoji
guarda solo il testo che Claude ha appena scritto: le emoji che avevi già messo in un file restano.

## 2026-10-13 — Telemetria minima, e /segnala arriva da sola

**Cosa cambia**: Arturo comincia a mandare a chi lo mantiene pochi dati d'uso anonimi. Sono
sempre gli stessi: l'avvio di una sessione, il nome dei comandi di Arturo che usi, il nome della
guardia che ti ha fermato, l'esito di `/aggiorna` e il tipo delle segnalazioni. Partono con un id
casuale, la versione e il sistema operativo, con il giorno e mai l'ora. È accesa di default.
In più `/segnala` non ti chiede più di mandare una email a mano. Dopo il tuo sì, la segnalazione
arriva direttamente a chi mantiene Arturo. Se la rete non risponde, parte da sola alla sessione dopo.

**Il principio dietro**: questo cambia una promessa. Fino a oggi l'Impegno 3 del README diceva
"Niente telemetria", e la novità di stamattina diceva che `/segnala` non era telemetria. Chi
mantiene Arturo ha deciso di cambiarla, perché senza dati d'uso non vede dove le persone si
bloccano. Le persone per cui Arturo è fatto spesso non lo sanno dire, e di sicuro non aprono una
issue. Il nuovo Impegno 3 dice cosa parte, cosa non parte mai e come spegnerla.

**Da sapere**: non partono mai prompt, file, percorsi, nomi, risposte o il tuo percorso a tappe.
Il server è open source (`server/`) e non salva il tuo indirizzo IP. Vedi cosa parte con
`python3 ~/.claude/bin/arturo telemetria mostra` e la spegni con
`python3 ~/.claude/bin/arturo telemetria spegni` oppure con `DO_NOT_TRACK=1`. Alla prima
sessione dopo l'aggiornamento Claude te lo dice una volta. Per far cancellare i tuoi dati scrivi
a federico@stellakamikaze.org con il tuo id.

## 2026-10-13 — Dire ad Arturo cosa non va, con /segnala

**Cosa cambia**: c'è un comando nuovo, `/segnala`. Lo usi quando qualcosa di Arturo non funziona,
quando hai un'idea o quando vorresti collegare uno strumento che usi nel lavoro. Claude scrive il
testo con te, toglie nomi, clienti e segreti, e te lo fa leggere. Parte solo con il tuo sì: come
issue su GitHub se hai un account, altrimenti come email a chi mantiene Arturo. Arturo poi te lo
propone da solo: subito dopo un intoppo, con il testo già pronto, e a fine sessione con una
domanda breve, al massimo una volta a settimana.

**Il principio dietro**: Arturo migliora con quello che gli dicono le persone che lo usano.
Una cosa che ti ha fatto perdere tempo, raccontata in tre righe, diventa una correzione per tutti.

**Da sapere**: non è telemetria. Niente parte senza che tu abbia visto il testo e detto sì. La
issue su GitHub è pubblica, la email arriva solo a chi mantiene Arturo. Una copia di ogni
segnalazione resta sul tuo computer, in `~/.claude/data/segnalazioni/`. Se non vuoi gli inviti:
`python3 ~/.claude/bin/arturo segnala basta`. `/segnala` resta lì quando ti serve.

## 2026-10-12 — Anche il sync fra le tue macchine passa dalla copia di prova

**Cosa cambia**: se hai un tuo repository, `/inizio` scarica le modifiche delle tue altre macchine
come fa ora `/aggiorna`: le prova in una copia a parte e le porta dentro solo se la config resta
integra. Se due macchine hanno cambiato le stesse righe, i tuoi file restano com'erano e il
conflitto aspetta nella copia di prova. Claude te lo mostra e lo risolvete insieme.

**Il principio dietro**: lo stesso di `/aggiorna`. I file che Claude Code sta usando cambiano solo
quando il risultato è già controllato.

**Da sapere**: il sync fra le tue macchine non finisce nel registro di `/aggiorna indietro`, che
torna indietro solo sugli aggiornamenti di Arturo.

## 2026-10-12 — Aggiornare senza mai rompere i file in uso

**Cosa cambia**: `/aggiorna` non unisce più l'aggiornamento dentro `~/.claude`. Lo prova in una copia
a parte, controlla lì la config, e porta dentro solo un risultato integro. Se le tue modifiche e
quelle di Arturo vanno in conflitto, i tuoi file restano com'erano, senza segni di conflitto:
Claude ti mostra il conflitto nella copia di prova, lo risolvete insieme lì e poi lo porta dentro.
In più la procedura che applica l'aggiornamento arriva con l'aggiornamento stesso: una correzione
alla procedura vale già dal primo giro. Prima, un conflitto poteva lasciare i segni dentro
`settings.json` e negli hook, e Claude Code spegneva le guardie senza dirlo.

**Il principio dietro**: i file che Claude Code sta usando cambiano solo quando il risultato è già
controllato.

**Da sapere**: questo aggiornamento lo applica ancora la procedura che hai installato. La copia di
prova vale dal giro successivo. Se `/aggiorna` ti dice che la config è già rotta, c'è un merge o un
pull rimasto a metà da prima: sistemalo con Claude prima di aggiornare.

## 2026-10-09 — Aggiornare con modifiche non salvate: si ferma e te lo dice

**Cosa cambia**: se hai cambiato un file della config senza salvarlo con un commit (lo fa anche
`/setup` in `settings.json`), `/aggiorna` non applica niente e `/inizio` non scarica dal tuo
repository. Ti dicono quali file sono e cosa fare: li salva `/fine`, poi riprovi. Prima
l'aggiornamento poteva lasciare `settings.json` con i segni di un conflitto e le guardie spente,
dicendo che era tutto a posto. Ora il messaggio "ho riportato la copia a prima" compare solo se è
vero. In più `/aggiorna` mostra le guardie e prende gli aggiornamenti da `upstream` anche quando
hai un tuo repository.

**Il principio dietro**: un comando che fallisce lo dice, e non dice mai "fatto" senza controllare.

## 2026-10-09 — Cinque mod nuovi: segreti, Bash, menu, cache, agenti

**Cosa cambia**: in `skills/` arrivano cinque mod che Claude Code carica da solo.
- `redazione-segreti`: se nell'output di un tool c'è una chiave, un token o la password di un database,
  Claude vede solo la sua forma (tipo, lunghezza, prime cifre dell'hash). Il valore resta sul tuo computer.
- `riscrivi-bash`: due comandi che sul Mac fallivano sempre ora vengono corretti prima di partire.
- `menu-contesto`: quando Claude ti propone un menu, il testo che lo precede si legge in un pannello.
- `cache-fredda`: sotto il prompt compare un avviso quando la cache è scaduta e il prossimo messaggio
  costerebbe come rileggere tutta la conversazione. È il momento giusto per chiedersi se serve una
  sessione nuova.
- `agent-flow` (`/agent-flow`): un pannello con l'albero degli agenti al lavoro, per capire come
  Claude divide un compito, cosa passa a ognuno e cosa torna indietro. Viene da un altro autore: è una
  copia fissata, letta riga per riga, che non si aggiorna da sola.

**Il principio dietro**: sono i mod che chi sviluppa Arturo usa ogni giorno, tolti i riferimenti
personali. I segreti non entrano più nella conversazione invece di essere segnalati dopo. Gli avvisi
arrivano solo quando c'è qualcosa da fare.

**A chi serve**: a tutti, senza fare niente. Per spegnerne uno: `/plugin`.

---

## 2026-10-04 — Il tavolo dei progetti

**Cosa cambia**: la pagina delle cose da fare (`arturo web`) ora parte dai progetti. In cima trovi
"Da dove partirei": un todo solo, scelto con una regola fissa, e il motivo in parole ("Sblocca #7",
"Scade domani"). Sotto, un foglio per ogni progetto, con il prossimo passo, gli altri todo in vista,
chi agisce e la scadenza più vicina. Davanti stanno i progetti dove qualcosa chiede te, dietro quelli
tutti in mano a Claude. Un foglio si apre e diventa la pagina del progetto. Lì un todo si apre nel
dettaglio, con le note datate, la storia di ogni passaggio e quello che aspetta o sblocca. In testa
c'è anche una riga con la tappa del tuo percorso.

**Il principio dietro**: il modo in cui chi sviluppa Arturo riparte ogni mattina. Prima la cosa da
cui partire, poi i progetti uno per uno, ogni todo con il segno di chi agisce. La regola di "Da dove
partirei" è la stessa per ogni vista: prima quello che chiede una persona, poi quello che sblocca
altri todo, poi scadenze e priorità.

**A chi serve**: a chi ha più di un progetto aperto e vuole vedere da dove ripartire senza leggere
l'elenco intero.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-04 — Claude ti dice quale skill usa

**Cosa cambia**: nel brief che Claude mostra prima di ogni lavoro c'è una riga nuova, "Skill:".
Dice quale skill userà e perché, oppure "nessuna". Se una skill che non hai nominato fa meglio il
lavoro, te lo dice lì. Il brief si carica anche più leggero: la parte per scrivere prompt destinati
ad altri strumenti (ChatGPT, Midjourney e simili) ora si legge solo quando la chiedi. In `/setup`
ci sono due regole consigliate in più per il tuo `CLAUDE.md`: l'ultima riga di ogni lavoro dice il
prossimo passo, e un risultato visivo è "fatto" solo quando Claude l'ha aperto come lo vedrai tu.

**Il principio dietro**: l'harness si misura su come lo usi. Le due regole e la riga Skill vengono
dall'analisi di due mesi d'uso reale di chi sviluppa Arturo: "e adesso?" chiesto 59 volte, il
"fatto" non verificato come correzione più frequente sui lavori visivi.

**A chi serve**: a chi non sa ancora quali skill ha, e a chi vuole capire dal brief se Claude ha
preso la strada giusta prima che cominci.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

---

## 2026-10-03 — Il percorso a tappe

**Cosa cambia**: chiedi a Claude "a che punto sono?" oppure scrivi `/percorso`. Vedi la tua
tappa fra quattro: Osserva, Prova, Delega, Orchestra. Accanto a ogni tappa c'è il numero del todo
che la prova, così puoi controllare. Vedi anche la lista "Cose che tieni per te" e un esercizio
della settimana sul tuo lavoro vero. `/inizio` ti mostra la tappa in una riga. A fine sessione
`/fine` può proporti una sola delega, e dopo un tuo no tace per qualche giorno.

**Il principio dietro**: automatizza la forma, frena l'impegno. Il percorso conta le decisioni
che tieni, non il lavoro che deleghi. Le tappe si aprono con una decisione presa prima che Claude
lavori, un limite che dichiari o un no motivato. Delega chiede due segni insieme: una decisione
presa prima che Claude lavori (con `deciso`, o chiudendo tu un todo DECIDI TU) e un limite (un
perché detto da te su un todo tuo, oppure un no motivato). Il nuovo capitolo "Tieni la decisione" lo
racconta (`docs/principi/05-tieni-la-decisione.md`), e `docs/esercizi.md` ha otto esercizi.

**Da sapere**: il percorso si calcola solo sul tuo computer, dai tuoi todo, e il suo stato resta lì.
I todo da cui nasce (i perché e le note "Tenuto:") viaggiano come gli altri todo: solo verso il
tuo repository privato, con `/fine`. Il referente della tua organizzazione non vede il percorso. Dopo un no alla proposta di `/fine`, Claude tace
tre giorni. Dopo due no di fila, due settimane. "Basta suggerimenti" le spegne finché non dici
"riprendi i suggerimenti". Pausa e silenzi valgono solo sul computer dove li dici: lo stato del
percorso non viaggia con `/fine`.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — Il pannello delle cose da fare

**Cosa cambia**: scrivi `/dafare` e dentro Claude Code si apre un pannello con le tue cose da
fare, divise in TOCCA A TE, DECIDI TU, FACCIO IO e FERMO. Ogni riga dice il progetto e la
scadenza. Scegli una riga con il numero e premi una lettera: `f` fatto, `s` ferma, `r` riprendi,
`c` chi lo fa, `a` avvicina, `l` allontana. `p` mostra un progetto alla volta. Quando hai cose
aperte, sopra il prompt compare una riga sottile: "3 cose da fare · /dafare per vederle".

**Il principio dietro**: vedere in ogni momento cosa è in mano tua e cosa in mano a Claude, e
agire senza scrivere comandi. Il pannello non ha un archivio suo: scrive con la stessa CLI
`arturo todo` che usa Claude, quindi le due viste dicono sempre la stessa cosa.

**Da sapere**: Esc chiude il pannello, `u` annulla l'ultimo tasto. Se i tasti non rispondono
più, premi ctrl+x tab oppure riscrivi `/dafare`. `/dafare nascondi` spegne la riga sopra il
prompt, `/dafare mostra` la riaccende. Il pannello chiede Claude Code 2.1.287 o successivo:
`/setup` controlla la versione. Arriva con l'aggiornamento e c'è dopo la riapertura di Claude
Code.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — La pagina delle cose da fare

**Cosa cambia**: ora vedi i tuoi todo anche in una pagina del browser. Chiedi a Claude "fammi
vedere le mie cose da fare in una pagina", oppure scrivi nel terminale
`python3 ~/.claude/bin/arturo web` (solo `arturo web` se con `/setup` hai aggiunto il comando breve). Da lì aggiungi un todo, lo segni fatto, lo modifichi o lo
fermi. Su un todo di "Decidi tu, poi faccio io" premi "Ho deciso", scrivi la scelta e il lavoro
passa a Claude. Dopo ogni azione compare "Annulla", salvo dopo una nota. Niente si
cancella dall'archivio.

**Il principio dietro**: lo stesso archivio, più modi di guardarlo. La pagina non tiene dati suoi
e segue le stesse regole di `arturo todo`: quello che fai nella pagina lo vede Claude, e quello
che scrive Claude compare nella pagina entro 20 secondi.

**Da sapere**: la pagina è facoltativa e gira solo sul tuo computer. Il link contiene una chiave
che cambia a ogni avvio, e la pagina non si collega a internet. Si spegne da sola dopo 30 minuti
senza la pagina aperta, oppure con il bottone "Spegni la pagina".

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — Le tue cose da fare, in un posto solo

**Cosa cambia**: quando dici a Claude "ricordami di mandare il preventivo venerdì", il todo
finisce in un archivio sul tuo computer e ci resta. Prima i task sparivano a fine sessione, e
sopravviveva solo la tabella dell'handoff. Ogni todo sa di quale progetto è, quando scade e chi
agisce: tu, tu che decidi e poi Claude, oppure Claude. `/fine` ci scrive quello che resta da
fare, `/inizio` te lo mostra diviso in TOCCA A TE, DECIDI TU, FACCIO IO e FERMO. Dal terminale
lo leggi con `python3 ~/.claude/bin/arturo todo` (con `/setup` puoi aggiungere il comando breve
`arturo todo`). Quando hai deciso su un todo di DECIDI TU, dillo a Claude, oppure scrivi
`python3 ~/.claude/bin/arturo todo deciso 4 "piano B"`: la scelta resta nel todo e il lavoro passa
a Claude.

**Il principio dietro**: delegare vuol dire anche sapere sempre cosa è in mano tua e cosa in
mano a Claude. Un elenco unico, con chi agisce scritto accanto a ogni cosa, rende visibile
questa divisione. È la base delle prossime viste: un pannello dentro Claude Code e una pagina web.

**Da sapere**: i todo stanno in `~/.claude/data/todo/` e nessun aggiornamento li tocca. Viaggiano
tra i tuoi computer solo se il repository della tua config è privato.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-09-30 — Lo strato della tua organizzazione

**Cosa cambia**: se lavori in un'organizzazione, Arturo ora può diventare "vostro". Il
**referente**, una persona del team, prepara con `/strato crea` uno strato con chi siete, come
scrivete, i lavori che si ripetono e i dati che non devono uscire. I colleghi lo ricevono con
`/strato installa` e lo tengono aggiornato con `/aggiorna`. All'avvio Claude sa per chi lavora, la
voce dell'organizzazione è una skill, e prima di mandare fuori un dato riservato chiede conferma.

**Il principio dietro**: uno strumento entra in un'organizzazione quando qualcuno del team lo
adatta al lavoro vero, non quando ognuno lo configura da solo. Lo strato vive nel repository
privato dell'organizzazione, separato da Arturo: gli aggiornamenti dei due non si pestano i piedi.

**Da sapere**: la guida del ruolo è in `docs/referente.md`. Lo strato è un plugin di Claude
Code: dopo l'installazione va riaperto Claude Code.

## 2026-09-30 — Aggiornamenti che non rompono niente, cartelle protette

**Cosa cambia**: tre cose che senti subito.

1. **Cancellare una cartella chiede sempre conferma.** Prima Arturo proteggeva solo la
   sua configurazione e la cartella dei progetti: una cartella di capitoli, la Scrivania
   o i Documenti si potevano cancellare senza domande. Ora ogni cancellazione di una
   cartella intera ti chiede il sì, tranne le cartelle che un programma ricrea da solo
   (per esempio `node_modules` o `dist`) e i file temporanei.
2. **Solo `/aggiorna` applica gli aggiornamenti.** `/inizio` e l'avvio li controllano e
   basta. `/aggiorna` ti dice quale versione hai e quale arriva, ti racconta cosa cambia
   nelle guardie, e se qualcosa va storto annulla da solo: la tua copia non resta mai a
   metà. `/aggiorna indietro` funziona anche dopo un `/fine`, e un secondo
   `/aggiorna indietro` torna ancora più indietro.
3. **Auto mode.** Claude Code ora giudica ogni comando con il suo classificatore, e le
   guardie di Arturo restano sopra di lui. Meno domande su lavoro normale, le stesse
   domande sulle azioni che non si annullano.

Anche: `/debug` ora si chiama `/diagnosi`, per non nascondere il `/debug` di Claude
Code. `/progetto` ha un ramo per chi non scrive codice (un libro, una ricerca, un
corso). Le emoji nei tuoi testi restano: il controllo vale solo per il codice.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer.
Per questo passa da una porta sola, dopo il tuo sì, e deve poter tornare indietro
sempre. Un `settings.json` rotto spegne tutte le guardie senza dire niente: Arturo ora
lo controlla all'avvio, prima e dopo ogni aggiornamento, e prima di ogni `/fine`.

**Da sapere**: dopo questo aggiornamento chiudi e riapri Claude Code. Se all'avvio vedi
una riga `CONFIG ROTTA`, fermati e chiedi a Claude di sistemarla prima di lavorare. Su
Windows Arturo funziona solo dentro Git Bash: `/setup` ora lo controlla.

## 2026-09-16 — Dove segnalare un problema

**Cosa cambia**: segnalare un problema ora ha una strada guidata. Quando apri una
issue su GitHub trovi due moduli pronti: "Qualcosa non funziona" (cosa stavi
facendo, cosa ti aspettavi, cosa è successo) e "Una proposta" (quale problema
vuoi risolvere). Nessuna domanda tecnica obbligatoria. Se invece trovi un
segreto esposto o un modo per aggirare una guardia, il modulo te lo dice subito:
non aprire una issue pubblica, usa la procedura privata in `SECURITY.md`, col
pulsante "Report a vulnerability" nella scheda Security del repository.

**Il principio dietro**: una segnalazione di sicurezza pubblica avvisa anche chi
potrebbe approfittarne. Il canale privato protegge tutti gli utenti mentre il
problema viene chiuso. Il resto delle segnalazioni resta pubblico e semplice:
chi apre una issue può non essere tecnico, quindi i moduli chiedono fatti, non
diagnosi. Tutto questo senza toccare l'impegno sulla telemetria: Arturo non
aggiunge contatori; chi mantiene misura l'uso solo dai dati pubblici di GitHub,
come scritto in `docs/manutenzione.md`.

**Da sapere**: se in passato hai aperto una issue per un falso positivo di una
guardia, quella strada non cambia: resta una issue normale, col comando esatto.
In privato va solo ciò che non deve diventare pubblico.

## 2026-09-16 — I tuoi file restano tuoi

**Cosa cambia**: ora c'è un confine chiaro tra i file di Arturo e i file tuoi. Il tuo
`CLAUDE.md` e i tuoi host fidati non vivono più dentro i file che gli aggiornamenti
sostituiscono. Gli host personali si scrivono in `hooks/hosts-interni.local`, una voce per
riga (hostname o rete): le due guardie anti-esfiltrazione lo leggono e non chiedono più
conferma verso quei server. `/setup` (FASE 6) guida su quel file invece di modificare i
`.py`, e il README ha una tabella che dice cosa arriva con gli aggiornamenti e cosa resta
tuo.

**Il principio dietro**: una personalizzazione scritta dentro un file di Arturo è una
modifica che il prossimo aggiornamento può travolgere o mandare in conflitto. Spostandola
in un file tuo, ignorato da git, l'aggiornamento non la tocca più. Il file sta dentro
`hooks/` di proposito: le guardie esistenti proteggono ogni scrittura lì sotto, quindi un
prompt malevolo non può aggiungere un host fidato senza la tua conferma.

**Da sapere**: se in passato hai aggiunto un host dentro `exfil-guard.py` o
`web-egress-guard.py`, al prossimo `/aggiorna` quella modifica può entrare in conflitto:
sposta la riga in `hooks/hosts-interni.local` e accetta la versione nuova dei due file.

## 2026-09-16 — Tornare indietro dopo un aggiornamento

**Cosa cambia**: `/aggiorna indietro` riporta la tua copia alla versione di prima dell'ultimo
aggiornamento. Prima di toccare qualunque cosa ti mostra in parole semplici cosa torna indietro — i
commit arrivati e le novità che spariranno — e lo fa solo dopo il tuo sì. In più, l'avviso di
avvio "la config è AVANTI di N commit" non compare più se il tuo `origin` è il repo originale di
Arturo: su quel repo non puoi scrivere, quindi i commit locali sono normali e l'avviso era solo
rumore. Se `origin` è un repo tuo, l'avviso resta.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer (vedi
"Cosa non è neutro"): la scelta è tua solo se puoi anche tornare indietro. E un avviso che non
puoi risolvere — come "non hai pushato" su un repo dove non puoi pushare — insegna a ignorare
gli avvisi.

**Da sapere**: il punto di ritorno si salva quando fai `/aggiorna`. Se non hai ancora fatto un
aggiornamento con questa versione, `/aggiorna indietro` ti dice che non c'è nulla da annullare.
Le modifiche ai tuoi file non si perdono: se un tuo file è toccato anche dall'aggiornamento,
il ritorno si ferma e te lo dice, invece di forzare. Dopo il ritorno, chiudi e riapri Claude
Code. Come si rilascia una versione — per chi mantiene Arturo o ne fa un fork — ora è scritto
in `docs/manutenzione.md`.

## 2026-09-16 — Cosa non è neutro, e cosa Arturo promette

**Cosa cambia**: il README si apre con tre sezioni nuove. **In breve** dice per chi è Arturo e come
cominciare in tre passi. **Cosa non è neutro** dice che Claude Code è un servizio a pagamento di
un'azienda privata, che quello che scrivi passa dai suoi server, e che un aggiornamento di Arturo è
codice di altri che gira sul tuo computer. **Impegni** dice cosa puoi aspettarti: repository
pubblico e MIT, niente telemetria, Arturo in italiano, e un avviso scritto se lo sviluppo si ferma.

**Il principio dietro**: chi usa uno strumento ha diritto di sapere chi lo controlla e cosa gli
viene promesso, prima di dipenderne. È lo stesso principio del capitolo 00 del curriculum, portato
sulla prima pagina.

**Da sapere**: `/inizio` scarica e applica gli aggiornamenti quando apri un progetto. Se preferisci
decidere tu ogni volta, usa `/aggiorna`, che ti chiede conferma prima di applicare.

## 2026-09-16 — L'avviso di aggiornamento, `/aggiorna` e `/guidami`

**Cosa cambia**: all'avvio della sessione Arturo ti dice quando c'è una versione nuova, come fa
Claude Code: `ARTURO: c'e' un aggiornamento (3 commit) — scaricalo con /aggiorna`. Il comando
**`/aggiorna`** ti mostra cosa arriva, controlla che non travolga i file che hai modificato tu e
applica solo dopo il tuo sì. Arriva anche **`/guidami`**: guarda gli ultimi handoff e le
conversazioni recenti e ti propone tre o quattro cose che ha senso fare adesso, con il motivo e il
primo passo, scartando quello che nel frattempo hai già fatto.

**Il principio dietro**: il controllo degli aggiornamenti leggeva solo quello che era già sul disco.
Senza un `git fetch` restava fermo per sempre, e chi non lanciava `/inizio` non vedeva mai una
novità: il canale c'era, ma non arrivava a nessuno. Ora il fetch parte da solo all'avvio, in
background e al massimo ogni sei ore, così l'avvio non aspetta la rete.

**Da sapere**: dopo un aggiornamento, chiudi e riapri Claude Code. Comandi, hook e skill si leggono
all'avvio della sessione: finché non riapri, quello che è appena arrivato non c'è.

---

## 2026-09-16 — Il prompt prima del brief, e il promemoria a ogni richiesta

**Cosa cambia**: `prompt-master` non mostra più solo il brief. Prima mostra il **prompt**: la tua
richiesta riscritta come Arturo la eseguirà, in una o due frasi. Poi il brief, come prima. E l'hook
`inject-now.sh` aggiunge a ogni messaggio una riga che ricorda la regola, così non vive solo nel
`CLAUDE.md`.

**Il principio dietro**: un brief dice cosa l'assistente farebbe, non da quale lettura della tua
richiesta nasce. Se ha capito un'altra cosa, il brief ti sembra comunque sensato e te ne accorgi a
lavoro finito. Il prompt mostrato sposta il controllo all'inizio, dove costa una riga.

**Per spegnerlo**: cancella il blocco `cat` finale di `hooks/inject-now.sh`. Se l'aderenza alla
regola non migliora, il promemoria va tolto, non irrobustito: sarebbe uno scaffold che non
compensa niente.

---

## 2026-09-13 — Seconda passata: dati, sincronizzazione, audit e licenza

**Cosa cambia**: la guardia sui dati riconosce `docker compose -f … down -v` e non si fa ingannare da un `WHERE` dentro una stringa SQL. Se crei un tuo repository privato, `/setup` tiene Arturo come `upstream` e `/inizio` ne scarica gli aggiornamenti, così `/novita` continua a raccontarli. `/fine` non committa con il validate rosso, segnala gli errori di staging e ritenta i push rimasti indietro. L'audit legge i path fra virgolette e controlla anche statusline e `defaultMode`. I tool GitHub via MCP passano da soli solo quando leggono. `/novita` segna ogni entry appena raccontata, per data e titolo, così una lettura interrotta non ne salta nessuna. Arturo ha ora una licenza MIT (`LICENSE`).

**Il principio dietro**: una guardia che cede a una variante comune del comando non protegge, e un canale di aggiornamento che perde una voce non informa. I controlli si scrivono sul comportamento vero, non sulla forma più comoda da riconoscere.

---

## 2026-09-13 — Guardie aggiornate, errori visibili

**Cosa cambia**: Arturo distingue il vero hostname da userinfo, porta e sottostringhe. Un URL che sembra interno può quindi essere esterno. Il dispatcher trasforma crash e output spurio delle guardie in una richiesta di conferma. Il gate di validazione conserva il codice del comando che produce l'output: un test fallito ferma il lavoro.

**Tre porte chiuse**: un file di unlock creato con Write o Edit chiede conferma come quello creato da shell, altrimenti l'assistente potrebbe sbloccarsi da solo. `gh api` chiede conferma quando scrive: mutazioni GraphQL, query lette da file, POST anche impliciti. `/fine` scrive l'handoff solo nello store della config e lo sincronizza solo verso un remote privato: in un progetto pubblico decisioni e note non entrano più nella storia Git.

**Potature**: spariscono i wrapper di comandi, skill e agenti approvati come duplicati, oltre al content guard GitHub e ai controlli PostToolUse non vincolanti. Restano le guardie distruttive e gli strumenti pedagogici.

**Il principio dietro**: una guardia deve identificare il destinatario reale. Un controllo deve riportare l'esito reale. Se non può provarlo, deve fermarsi.

---

## 2026-09-02 — La porta e la procedura: description, when_to_use e le sezioni "Freni"

**Cosa cambia**: ogni skill ha ora due campi in testa. `description` dice in una frase che cosa
la skill produce; `when_to_use` dice quando si accende — le frasi che dici davvero, i casi in cui
NON si accende e a chi passa la palla — e chiude sempre con "Segui tutti i passi nell'ordine: non
prendere scorciatoie basandoti su questa description". Nel corpo, la prima cosa dopo il titolo è
un passo o un prerequisito, non una spiegazione; le regole che non si possono saltare stanno sotto
un'intestazione propria, `## Freni` o `## Importante`. Due skill nuove: `prompt-master` (mostra un
brief di otto righe prima di ogni lavoro: obiettivo, output, vincoli, quando è fatto, assunzioni,
cosa chiarire) e `italiano-semplificato` (riscrive un testo con frasi corte e senza burocratese).
`/setup` propone entrambe le regole nel tuo `CLAUDE.md`; `/inizio` fa il pull con `--autostash`,
così un file sporco non blocca più l'aggiornamento.

**Il principio dietro**: il modello legge la `description` per decidere se una skill si applica —
e se lì trova i passi, li esegue senza aprire il corpo, saltando le regole. Quindi la porta dice
solo *se entrare*; la procedura sta dentro. E due domande valgono più di dieci regole: "se un
agente leggesse solo la description, cosa farebbe?" (deve rispondere: decide se serve) e "cosa
farebbe un agente pigro se questa skill non esistesse?" (il corpo deve impedire proprio quello).
Idee prese da `gsarig/skills`, applicate qui alla lettera.

**A chi serve**: a chi scrive o modifica una skill, e a chi si chiede perché una skill non è
partita quando doveva — il primo sospetto è la frase in `when_to_use`. Prova: `/sparring` sul
principio "la porta e la procedura" con una skill che usi spesso.

---

## 2026-08-19 — Chiedere bene: il capitolo 01 e i punti dove l'harness lo pretende

**Cosa cambia**: il curriculum ha un secondo capitolo disponibile,
`docs/principi/01-chiedere-bene.md` — la forma di una richiesta che funziona (da dove
parto, cosa è cambiato, cosa chiedo) e come si dichiara che il lavoro è finito. In più tre
comandi ora lo pretendono dove serve: `/discovery` chiede che i criteri di successo siano
risultati osservabili e non intenzioni, `/write-plan` fa aprire ogni fase con l'effetto che
produce, `/debug` chiede che l'ipotesi sia formulata in modo da poter essere smentita da una
verifica sì/no. Gli agenti che scrivono (`drafter`, `synthesizer`) mettono la conclusione in
cima invece che in fondo.

**Il principio dietro**: il modello risponde alla domanda che gli hai fatto, non a quella che
avevi in testa — e quando il contesto manca se lo inventa, in modo convincente. Formulare la
richiesta è la parte del lavoro che resta tua, non scade con la versione dello strumento, e
vale anche con le persone. L'altra metà dello stesso principio è dire come si riconosce che è
fatto: senza un risultato osservabile, "fatto" è un'opinione.

**Ti riguarda se**: ti è capitato di ricevere una risposta ben scritta e fuori bersaglio, o
di accorgerti a lavoro finito che "finito" voleva dire due cose diverse per te e per
l'assistente. La numerazione del curriculum è cambiata: i tre capitoli annunciati prima
(rail, orchestrazione, memoria) sono ora 02, 03 e 04.

**Per provarlo**: leggi `docs/principi/01-chiedere-bene.md` — sono dieci minuti — poi
`/sparring chiedere bene` per riscrivere insieme una richiesta vera, magari una che era
andata storta.

---

## 2026-08-17 — Nasce il canale novità, lo sparring e il curriculum dei principi

**Cosa cambia**: Arturo ora è un harness che ti tiene aggiornato. Tre pezzi nuovi:
`/novita` (questo canale: dopo ogni aggiornamento ti racconta cosa è cambiato e perché),
`/sparring` (una sessione guidata che parte da un principio e lo prova sui TUOI casi
d'uso, con esperimenti piccoli e reversibili), e la cartella `docs/principi/` — il
curriculum: i principi dell'usare bene un'AI, spiegati in semplice, per chi non fa un
mestiere tecnico.

**Il principio dietro**: uno strumento che impari una volta sola invecchia con te. Questo
campo cambia in fretta: quando un modo di lavorare nuovo diventa importante, l'harness si
aggiorna per tutti — e tu scopri la novità con il suo perché, non con un changelog di
sigle.

**Ti riguarda se**: usi Arturo e vuoi che continui a valere anche fra sei mesi; oppure
sei all'inizio e vuoi una strada per imparare i principi, non solo i comandi.

**Per provarlo**: leggi il primo capitolo del curriculum,
`docs/principi/00-chi-possiede-lo-strumento.md` — parte dalla domanda che viene prima di
ogni comando: di chi è lo strumento che stai imparando? Poi, se vuoi, `/sparring`.
