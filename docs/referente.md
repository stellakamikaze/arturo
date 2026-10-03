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

Arturo non raccoglie dati su come lo usate. Dopo 60 giorni la verifica la fate voi, con un
colloquio di mezz'ora. Lo strato funziona se:

- tu e almeno un collega lo usate ancora **ogni settimana** per un lavoro vero;
- almeno una skill dello strato è entrata nell'abitudine di qualcuno che non sei tu;
- le regole di scrittura hanno cambiato almeno un testo uscito dall'organizzazione.

Se nessuno lo usa più, chiedi perché prima di aggiungere altro: di solito manca una skill su un
lavoro che conta, oppure una regola chiede troppe conferme.

## Il pannello delle cose da fare: un mod

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

Se spegnete i mod, la persona perde solo il pannello e la riga sopra il prompt. La CLI
`arturo todo` e la skill todo restano.

## Il percorso a tappe: si calcola sul computer della persona

Arturo propone a ogni persona un percorso a tappe (`arturo percorso`, `/percorso`). Il percorso
conta le decisioni che la persona tiene per sé, non quanto lavoro delega. Si calcola sul suo
computer, dall'archivio dei suoi todo, e lo stato sta in `~/.claude/session-env/percorso.json`.
Il referente non vede il percorso dei colleghi: né lo strato né altri strumenti di Arturo lo
leggono o lo inviano. Se volete parlarne, chiedetelo alla persona nel colloquio dei 60 giorni.

I todo da cui nasce il percorso (i perché e le note «Tenuto:») viaggiano come gli altri todo:
`/fine` li manda solo al repository privato della config della persona. Se quel repository sta in
un'organizzazione, chi ha accesso al repository può leggere quelle note. Tenete la config di ogni
persona in un repository suo.

## Se vi serve un affiancamento

Arturo è gratuito e resta libero. Chi vuole essere affiancato nella costruzione dello strato e
nella formazione del referente può chiederlo a chi mantiene Arturo: i contatti sono nel README.
