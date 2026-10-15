# La guida del referente

Il **referente** è la persona che porta Arturo dentro un'organizzazione. Non serve che sappia
programmare. Serve che conosca il lavoro dei colleghi, che abbia voglia di provare, e che dedichi
allo strumento un po' di tempo ogni settimana.

Il referente cura lo **strato dell'organizzazione**: ciò che rende Arturo «vostro». Dentro ci
sono chi siete, come scrivete, i lavori che si ripetono e i dati che non devono uscire. I colleghi
lo installano una volta e lo ricevono aggiornato. Il comando è `/strato`.

## Il ruolo in una pagina

- **All'inizio**: crei lo strato (`/strato crea`), lo provi, lo pubblichi, inviti i colleghi.
- **Ogni settimana**: mezz'ora. Raccogli un lavoro che si è ripetuto e che Arturo può fare meglio,
  e lo trasformi in una skill. Correggi una regola di scrittura che non ha funzionato. Pubblichi.
- **Quando arriva un collega**: lo inviti al repository e gli dici di scrivere
  `/strato installa <indirizzo>`. La prima sessione la fate insieme.
- **Dopo 60 giorni**: la verifica (sotto).

## Prima di cominciare: l'account e il repository

Lo strato vive in un **repository privato** su GitHub (o GitLab). È il posto da cui i colleghi lo
ricevono, e solo le persone invitate lo possono leggere.

1. **Un account per l'organizzazione.** Su GitHub conviene creare un'organizzazione (gratuita per
   i repository privati di base): il repository resta dell'organizzazione anche se il referente
   cambia. In alternativa va bene l'account del referente.
2. **Il repository lo crea `/strato crea`**, privato. Se lo crei a mano dal sito, scegli
   «Private».
3. **Ogni collega ha bisogno di tre cose:** un account sul servizio, l'invito al repository
   (Settings → Collaborators, oppure il team dell'organizzazione) e il collegamento del suo
   computer all'account. L'ultimo passo lo guida `/strato installa`, con `gh auth login`.

## Quando un lavoro merita una skill

Un lavoro è **ricorrente** se torna ogni settimana o ogni mese, con la stessa forma: la rassegna,
il verbale, la scheda di progetto, la risposta a un bando, il report per un finanziatore. Il segno
più chiaro: qualcuno lo spiega ogni volta da capo, a voce o per email.

Per trasformarlo in skill, copia `plugins/strato/skills/modello-lavoro/` con un nome nuovo e
riempilo con Arturo. Una skill buona descrive **com'è un risultato buono e perché**, non solo una
lista di passi. Una skill per volta: provala su un caso vero prima di pubblicarla.

Nella cartella `esempi/` dello strato trovi tre esempi da adattare: una skill di posta che impara
dalle email inviate, una skill di recap che legge la trascrizione intera delle riunioni, e
un'anteprima prima dell'invio che legge le vostre regole da un file. Claude Code non li carica
finché non li copi in `plugins/strato/`: il `LEGGIMI` di ogni esempio dice come.

## Cosa non va mai nello strato

- **Password, token, chiavi.** Il repository lo leggono tutti i colleghi, e resta nella storia
  anche se il file viene cancellato. Il controllo segreti di Arturo prova a fermarli, ma non
  contarci.
- **Dati personali** di colleghi, clienti o persone con cui lavorate.
- **Nomi che non devono circolare**: vanno in `dati-riservati.txt` come parole da proteggere, non
  descritti in `ORGANIZZAZIONE.md`.

`dati-riservati.txt` elenca ciò che non deve uscire dal computer senza una conferma: progetti
riservati, cartelle, domini interni. Lo strato chiede conferma quando una di queste voci sta per
partire (un invio in rete, una pagina web, uno strumento che manda o condivide). Non controlla i
file che i colleghi scrivono: il lavoro sui progetti riservati resta libero.

## Come si cambia una regola

**Solo nel repository dello strato**, mai nei file installati sui computer dei colleghi: il
prossimo aggiornamento li sovrascrive. Il ciclo:

1. cambi il file nella cartella dello strato;
2. provi con `claude --plugin-dir plugins/strato`;
3. pubblichi con `/strato pubblica`;
4. i colleghi lo ricevono con `/aggiorna`, oppure da soli se hanno acceso l'aggiornamento
   automatico da `/plugin`.

## La verifica dei 60 giorni

La telemetria di Arturo va a chi mantiene Arturo, non a te, e non dice chi usa cosa (sezione
più sotto). Dopo 60 giorni la verifica la fate voi, con un colloquio di mezz'ora. Lo strato funziona se:

- tu e almeno un collega lo usate ancora **ogni settimana** per un lavoro vero;
- almeno una skill dello strato è entrata nell'abitudine di qualcuno che non sei tu;
- le regole di scrittura hanno cambiato almeno un testo uscito dall'organizzazione.

Se nessuno lo usa più, chiedi perché prima di aggiungere altro: di solito manca una skill su un
lavoro che conta, oppure una regola chiede troppe conferme.

## I mod: il pannello e la redazione dei segreti

Arturo porta un pannello dentro Claude Code: `/dafare`. È un **mod**, cioè un plugin che Claude
Code carica da solo dalla cartella `~/.claude/skills/dafare/`. Nell'elenco dei plugin si chiama
`dafare@skills-dir`. Il mod legge e scrive i todo solo con la CLI `arturo`, sul computer della
persona, e non manda niente in rete.

Le managed settings dell'organizzazione decidono se Claude Code carica i mod:

- Se usate un elenco chiuso di marketplace (`strictKnownMarketplaces`), Claude Code non carica i
  mod da `~/.claude/skills`. Per tenere il pannello, aggiungete all'elenco `{"source": "skills-dir"}`.
- Per spegnere i mod senza altre restrizioni, mettete `{"source": "skills-dir"}` in
  `blockedMarketplaces`.
- Una persona sola lo spegne con `claude plugin disable dafare@skills-dir`. Per la sola riga sopra
  il prompt basta `/dafare nascondi`.

Con la stessa regola Claude Code carica gli altri mod di Arturo, ognuno dalla sua cartella in
`~/.claude/skills/`. Due di loro proteggono. `redazione-segreti` sostituisce i segreti negli output
dei tool con la loro forma (tipo, lunghezza, hash) prima che Claude li legga. Anche `blast-radius`
protegge: ferma `rm -rf`, `git reset --hard` e un push forzato e mostra cosa cambierebbero. Gli altri
sono comodità: `cache-fredda`, `riscrivi-bash`, `apri` e `gws`.

Se spegnete i mod, la persona perde il pannello, la riga sopra il prompt **e la redazione dei
segreti**: Claude torna a leggere in chiaro un token stampato da un comando. Resta lo scanner
`credential-leak-scanner.py`, che avvisa dopo, quando Claude l'ha già letto. Se dovete spegnere i
mod, spegnete il solo pannello con `claude plugin disable dafare@skills-dir` e lasciate
`redazione-segreti@skills-dir` acceso. La CLI `arturo todo` e la skill todo restano in ogni caso.

## Il percorso a tappe: si calcola sul computer della persona

Arturo propone a ogni persona un percorso a tappe (`arturo percorso`, `/percorso`). Il percorso
conta le decisioni che la persona tiene per sé, non quanto lavoro delega. Si calcola sul suo
computer, dall'archivio dei suoi todo, e lo stato sta in `~/.claude/session-env/percorso.json`.
Il referente non vede il percorso dei colleghi: lo strato non lo legge. Alla telemetria di Arturo
partono solo numeri (la tappa, quante decisioni e limiti), mai cosa la persona ha scritto, e arrivano
a chi mantiene Arturo, non a te. Se volete parlarne, chiedetelo alla persona nel colloquio dei 60 giorni.

## La telemetria: a chi mantiene Arturo, non a te

Arturo manda a chi lo mantiene una telemetria accesa di default, che serve a correggere ogni
settimana i punti dove le persone si bloccano. Parte un elenco chiuso di eventi: l'avvio di una
sessione, il nome dei comandi di Arturo usati, il nome della guardia che ha fermato un comando o ha
chiesto conferma (e se la persona ha detto sì), una guardia che si è rotta, l'esito di `/aggiorna`,
la fase di `/setup` raggiunta, il tipo delle segnalazioni, i file e gli hook di Arturo che la persona
ha cambiato o spento (dei file solo la posizione dentro Arturo, che è pubblica), una config rotta, la
versione di Claude Code e i soli numeri del percorso a tappe. Con gli eventi partono un id casuale
creato da Arturo, la versione e il sistema operativo, con il solo giorno. Non partono mai prompt, file
della persona, percorsi del suo computer, nomi, risposte o testi del percorso. Lo strato dell'organizzazione e i suoi
comandi non entrano negli eventi: il nome di un comando si registra solo se il comando è di Arturo.

Il referente non riceve questi dati, e chi mantiene Arturo non sa a quale organizzazione appartiene
un'installazione. Oggi la telemetria si spegne persona per persona, con
`python3 ~/.claude/bin/arturo telemetria spegni` oppure con `DO_NOT_TRACK=1`. Se la vostra
organizzazione chiede di spegnerla, dillo ai colleghi al momento dell'installazione.
`python3 ~/.claude/bin/arturo telemetria mostra` fa vedere l'id e cosa parte. Le regole intere
stanno nell'Impegno 3 del README.

## Le segnalazioni: Arturo a chi lo mantiene, lo strato a te

`/segnala` manda a chi mantiene Arturo un problema, un'idea o un'integrazione, e solo dopo il sì
della persona. Non passa dal referente. Di default arriva direttamente a chi mantiene Arturo, per
email; diventa una issue pubblica su GitHub solo se la persona lo sceglie. Un problema dello
strato dell'organizzazione (una skill del mestiere, la voce, un collegamento interno) arriva a te:
`/segnala` lo riconosce e manda la persona da te, senza scrivere niente fuori.

I todo da cui nasce il percorso (i perché e le note «Tenuto:») viaggiano come gli altri todo:
`/fine` li manda solo al repository privato della config della persona. Se quel repository sta in
un'organizzazione, chi ha accesso al repository può leggere quelle note. Tenete la config di ogni
persona in un repository suo.

## Se vi serve un affiancamento

Arturo è gratuito e resta libero. Chi vuole essere affiancato nella costruzione dello strato e
nella formazione del referente può chiederlo a chi mantiene Arturo: i contatti sono nel README.
