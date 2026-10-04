# Novità

Questo file è il canale di aggiornamento di Arturo. Ogni volta che l'harness evolve in un
modo che vale la pena raccontare, qui compare una entry: cosa cambia, il principio dietro,
a chi serve. La entry più recente sta in cima, con data ISO nell'intestazione.

Non serve leggerlo a mano: dopo un `git pull`, all'avvio della sessione Arturo ti avvisa se
c'è qualcosa che non hai ancora visto, e `/novita` te lo racconta in parole semplici —
con la possibilità di fare sparring (`/sparring`) per capire se la novità serve al tuo
modo di lavorare.

---

## 2026-10-04 — Il tavolo dei progetti

**Cosa cambia**: la pagina delle cose da fare (`arturo web`) ora parte dai progetti. In cima trovi
«Da dove partirei»: un todo solo, scelto con una regola fissa, e il motivo in parole («Sblocca #7»,
«Scade domani»). Sotto, un foglio per ogni progetto, con il prossimo passo, gli altri todo in vista,
chi agisce e la scadenza più vicina. Davanti stanno i progetti dove qualcosa chiede te, dietro quelli
tutti in mano a Claude. Un foglio si apre e diventa la pagina del progetto. Lì un todo si apre nel
dettaglio, con le note datate, la storia di ogni passaggio e quello che aspetta o sblocca. In testa
c'è anche una riga con la tappa del tuo percorso.

**Il principio dietro**: il modo in cui chi sviluppa Arturo riparte ogni mattina. Prima la cosa da
cui partire, poi i progetti uno per uno, ogni todo con il segno di chi agisce. La regola di «Da dove
partirei» è la stessa per ogni vista: prima quello che chiede una persona, poi quello che sblocca
altri todo, poi scadenze e priorità.

**A chi serve**: a chi ha più di un progetto aperto e vuole vedere da dove ripartire senza leggere
l'elenco intero.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-04 — Claude ti dice quale skill usa

**Cosa cambia**: nel brief che Claude mostra prima di ogni lavoro c'è una riga nuova, «Skill:».
Dice quale skill userà e perché, oppure «nessuna». Se una skill che non hai nominato fa meglio il
lavoro, te lo dice lì. Il brief si carica anche più leggero: la parte per scrivere prompt destinati
ad altri strumenti (ChatGPT, Midjourney e simili) ora si legge solo quando la chiedi. In `/setup`
ci sono due regole consigliate in più per il tuo `CLAUDE.md`: l'ultima riga di ogni lavoro dice il
prossimo passo, e un risultato visivo è «fatto» solo quando Claude l'ha aperto come lo vedrai tu.

**Il principio dietro**: l'harness si misura su come lo usi. Le due regole e la riga Skill vengono
dall'analisi di due mesi d'uso reale di chi sviluppa Arturo: «e adesso?» chiesto 59 volte, il
«fatto» non verificato come correzione più frequente sui lavori visivi.

**A chi serve**: a chi non sa ancora quali skill ha, e a chi vuole capire dal brief se Claude ha
preso la strada giusta prima che cominci.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

---

## 2026-10-03 — Il percorso a tappe

**Cosa cambia**: chiedi a Claude «a che punto sono?» oppure scrivi `/percorso`. Vedi la tua
tappa fra quattro: Osserva, Prova, Delega, Orchestra. Accanto a ogni tappa c'è il numero del todo
che la prova, così puoi controllare. Vedi anche la lista «Cose che tieni per te» e un esercizio
della settimana sul tuo lavoro vero. `/inizio` ti mostra la tappa in una riga. A fine sessione
`/fine` può proporti una sola delega, e dopo un tuo no tace per qualche giorno.

**Il principio dietro**: automatizza la forma, frena l'impegno. Il percorso conta le decisioni
che tieni, non il lavoro che deleghi. Le tappe si aprono con una decisione presa prima che Claude
lavori, un limite che dichiari o un no motivato. Delega chiede due segni insieme: una decisione
presa prima che Claude lavori (con `deciso`, o chiudendo tu un todo DECIDI TU) e un limite (un
perché detto da te su un todo tuo, oppure un no motivato). Il nuovo capitolo «Tieni la decisione» lo
racconta (`docs/principi/05-tieni-la-decisione.md`), e `docs/esercizi.md` ha otto esercizi.

**Da sapere**: il percorso si calcola solo sul tuo computer, dai tuoi todo, e il suo stato resta lì.
I todo da cui nasce (i perché e le note «Tenuto:») viaggiano come gli altri todo: solo verso il
tuo repository privato, con `/fine`. Il referente della tua organizzazione non vede il percorso. Dopo un no alla proposta di `/fine`, Claude tace
tre giorni. Dopo due no di fila, due settimane. «Basta suggerimenti» le spegne finché non dici
«riprendi i suggerimenti». Pausa e silenzi valgono solo sul computer dove li dici: lo stato del
percorso non viaggia con `/fine`.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — Il pannello delle cose da fare

**Cosa cambia**: scrivi `/dafare` e dentro Claude Code si apre un pannello con le tue cose da
fare, divise in TOCCA A TE, DECIDI TU, FACCIO IO e FERMO. Ogni riga dice il progetto e la
scadenza. Scegli una riga con il numero e premi una lettera: `f` fatto, `s` ferma, `r` riprendi,
`c` chi lo fa, `a` avvicina, `l` allontana. `p` mostra un progetto alla volta. Quando hai cose
aperte, sopra il prompt compare una riga sottile: «3 cose da fare · /dafare per vederle».

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

**Cosa cambia**: ora vedi i tuoi todo anche in una pagina del browser. Chiedi a Claude «fammi
vedere le mie cose da fare in una pagina», oppure scrivi nel terminale
`python3 ~/.claude/bin/arturo web` (solo `arturo web` se con `/setup` hai aggiunto il comando breve). Da lì aggiungi un todo, lo segni fatto, lo modifichi o lo
fermi. Su un todo di «Decidi tu, poi faccio io» premi «Ho deciso», scrivi la scelta e il lavoro
passa a Claude. Dopo ogni azione compare «Annulla», salvo dopo una nota. Niente si
cancella dall'archivio.

**Il principio dietro**: lo stesso archivio, più modi di guardarlo. La pagina non tiene dati suoi
e segue le stesse regole di `arturo todo`: quello che fai nella pagina lo vede Claude, e quello
che scrive Claude compare nella pagina entro 20 secondi.

**Da sapere**: la pagina è facoltativa e gira solo sul tuo computer. Il link contiene una chiave
che cambia a ogni avvio, e la pagina non si collega a internet. Si spegne da sola dopo 30 minuti
senza la pagina aperta, oppure con il bottone «Spegni la pagina».

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — Le tue cose da fare, in un posto solo

**Cosa cambia**: quando dici a Claude «ricordami di mandare il preventivo venerdì», il todo
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

**Cosa cambia**: se lavori in un'organizzazione, Arturo ora può diventare «vostro». Il
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
issue su GitHub trovi due moduli pronti: «Qualcosa non funziona» (cosa stavi
facendo, cosa ti aspettavi, cosa è successo) e «Una proposta» (quale problema
vuoi risolvere). Nessuna domanda tecnica obbligatoria. Se invece trovi un
segreto esposto o un modo per aggirare una guardia, il modulo te lo dice subito:
non aprire una issue pubblica, usa la procedura privata in `SECURITY.md`, col
pulsante «Report a vulnerability» nella scheda Security del repository.

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
avvio «la config è AVANTI di N commit» non compare più se il tuo `origin` è il repo originale di
Arturo: su quel repo non puoi scrivere, quindi i commit locali sono normali e l'avviso era solo
rumore. Se `origin` è un repo tuo, l'avviso resta.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer (vedi
«Cosa non è neutro»): la scelta è tua solo se puoi anche tornare indietro. E un avviso che non
puoi risolvere — come «non hai pushato» su un repo dove non puoi pushare — insegna a ignorare
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

## 2026-09-02 — La porta e la procedura: description, when_to_use e le sezioni «Freni»

**Cosa cambia**: ogni skill ha ora due campi in testa. `description` dice in una frase che cosa
la skill produce; `when_to_use` dice quando si accende — le frasi che dici davvero, i casi in cui
NON si accende e a chi passa la palla — e chiude sempre con «Segui tutti i passi nell'ordine: non
prendere scorciatoie basandoti su questa description». Nel corpo, la prima cosa dopo il titolo è
un passo o un prerequisito, non una spiegazione; le regole che non si possono saltare stanno sotto
un'intestazione propria, `## Freni` o `## Importante`. Due skill nuove: `prompt-master` (mostra un
brief di otto righe prima di ogni lavoro: obiettivo, output, vincoli, quando è fatto, assunzioni,
cosa chiarire) e `italiano-semplificato` (riscrive un testo con frasi corte e senza burocratese).
`/setup` propone entrambe le regole nel tuo `CLAUDE.md`; `/inizio` fa il pull con `--autostash`,
così un file sporco non blocca più l'aggiornamento.

**Il principio dietro**: il modello legge la `description` per decidere se una skill si applica —
e se lì trova i passi, li esegue senza aprire il corpo, saltando le regole. Quindi la porta dice
solo *se entrare*; la procedura sta dentro. E due domande valgono più di dieci regole: «se un
agente leggesse solo la description, cosa farebbe?» (deve rispondere: decide se serve) e «cosa
farebbe un agente pigro se questa skill non esistesse?» (il corpo deve impedire proprio quello).
Idee prese da `gsarig/skills`, applicate qui alla lettera.

**A chi serve**: a chi scrive o modifica una skill, e a chi si chiede perché una skill non è
partita quando doveva — il primo sospetto è la frase in `when_to_use`. Prova: `/sparring` sul
principio «la porta e la procedura» con una skill che usi spesso.

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
fatto: senza un risultato osservabile, «fatto» è un'opinione.

**Ti riguarda se**: ti è capitato di ricevere una risposta ben scritta e fuori bersaglio, o
di accorgerti a lavoro finito che «finito» voleva dire due cose diverse per te e per
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
