---
name: prompt-master
description: >-
  Due modalità: PROMPT ESTERNO produce un prompt pronto da incollare in un altro tool AI; BRIEF
  INTERNO ricostruisce il contesto che una richiesta sintetica a Claude Code non contiene e lo mostra
  come brief verificabile prima di lavorare.
when_to_use: >-
  Usa il PROMPT ESTERNO quando l'utente chiede esplicitamente un prompt per ChatGPT, Gemini, Cursor,
  Midjourney, Sora, ElevenLabs, Codex o agenti di coding. Usa il BRIEF INTERNO PRIMA di ogni richiesta
  di lavoro rivolta a Claude Code, anche breve: il brief va sempre mostrato. NON per la conversazione
  pura: domande, commenti, risposte a un menu. Segui tutti i passi nell'ordine: non
  prendere scorciatoie basandoti su questa description.
version: 1.8.0
upstream: nidhinjs/prompt-master@2bd9251
---

## MODALITÀ BRIEF INTERNO — richieste rivolte a Claude Code

Si attiva su ogni richiesta di lavoro rivolta a Claude Code, anche breve. Non si attiva sulla conversazione pura: domande, commenti, risposte a un menu, spiegazioni senza nulla da fare. In caso di dubbio il brief si mostra: costa tre righe, e una richiesta capita male costa molto di più.

Casi di confine:

- **Una domanda che chiede un'azione è lavoro.** "Puoi fermare X e farlo partire su Y?", "fai una review di…", "verifica se…": il brief si mostra. Resta conversazione la domanda che chiede un parere o un fatto ("ci serve?", "c'è spazio?").
- **Il via libera a proposte già elencate è una risposta a un menu.** "vai", "procedi su tutto", "1+2+3", "tutti", "il resto sì": il brief l'hanno già avuto le proposte, non se ne scrive un altro.
- **Stop e comandi di controllo non passano mai dal brief.** "ferma", "interrompi", "stato", "un update al minuto": si esegue subito. Un brief prima di fermare un'operazione ritarda un'azione di sicurezza.
- **Una correzione a lavoro iniziato è una riga**, "Brief corretto: …". Una richiesta nuova ha il suo prompt e il suo brief, ma la skill non si ricarica: il corpo è già nel contesto.

### 1. Arricchimento (silenzioso)

Le richieste sono spesso sintetiche: il lavoro non è riformularle, è ricostruire il contesto operativo che non contengono. Il destinatario del contesto sei tu, non la persona. Prima di scrivere il brief recupera davvero:

- Il `CLAUDE.md` del progetto e l'handoff più recente in `~/.claude/data/handoffs/<progetto>/` (vedi `/inizio`)
- Stato reale: `git log --oneline -20`, file e sistemi che la richiesta tocca, cosa è già stato fatto
- Decisioni già chiuse che vincolano il lavoro: le regole del `CLAUDE.md` personale e di progetto, le convenzioni di voce e formato, gli errori già documentati, le note di memoria pertinenti (`arturo memoria cerca "parole"`)
- Vincoli tecnici e side-effect: cosa viene scritto, inviato, sovrascritto o speso

Le letture necessarie si fanno prima del brief. Leggi ciò che la richiesta tocca: quello che è già nel contesto della sessione non si rilegge. Un brief costruito su assunzioni non nutre, aggiunge rumore. In silenzio chiarisci compito, formato dell'output, vincoli, input, contesto, pubblico e criterio di successo.

### 2. Prompt e brief (mostrati insieme)

Non si mostra solo il brief: si mostra **prima il prompt**, cioè la richiesta della persona
riscritta come la eseguirai. È il pezzo che le permette di fermarti quando hai capito
un'altra cosa, e costa una riga. Il brief da solo dice cosa faresti, non da quale
lettura della richiesta nasce.

```
PROMPT
[la richiesta riscritta in una o due frasi: cosa la persona sta chiedendo, come lo eseguirai,
 su quali file o sistemi. Non la parafrasi delle sue parole: la loro traduzione operativa.]
```

Se la richiesta era già completa, il prompt è quasi identico all'originale: si mostra lo stesso,
una riga, e si va avanti. Se l'hai dovuta interpretare, il prompt è il punto in cui l'interpretazione
diventa visibile.

Sotto il prompt, la sintesi verificabile dell'arricchimento, in un blocco di massimo 8 righe. La profondità si adatta alla richiesta: per un comando singolo o una correzione puntuale bastano tre righe (obiettivo, output, fatto quando); per un lavoro che tocca più file, sistemi o side-effect servono tutte e sei. Scrivi solo le righe che portano informazione: una riga ovvia si omette, non si riempie di parole.

```
BRIEF
Obiettivo: [azione precisa, verbo concreto — non la parafrasi della richiesta]
Output: [forma, formato, dove finisce]
Vincoli: [cosa deve e non deve accadere; regole del CLAUDE.md applicabili]
Fatto quando: [criterio verificabile, binario dove possibile]
Skill: [/nome e perché in poche parole, oppure «nessuna»]
Assunzioni: [cosa sto dando per scontato]
Da chiarire: [max 3 punti]
```

- **La riga Skill è sempre presente.** Scegli dall'elenco delle skill di questa sessione per
  giudizio sul lavoro da fare, non per parole chiave. Se una skill che la persona non ha nominato
  fa meglio il lavoro di quella che ha chiesto, dillo qui. Se nessuna serve, scrivi "nessuna". Questa skill (prompt-master) non conta: c'è
  sempre.
- Il brief mostrato è la punta dell'arricchimento, non tutto: il contesto recuperato resta nel tuo ragionamento e nel lavoro che ne segue. Non trascriverlo per intero, e non trasformare il brief in un rapporto di ricerca.
- Se un'ambiguità cambierebbe materialmente il lavoro, chiedi prima di procedere, con una raccomandazione motivata. Max 3 punti. Il menu AskUserQuestion vale solo se il testo prima sta in una o due righe: dopo un brief di più righe, chiudi con l'elenco numerato e le parole di risposta in grassetto.
- In plan mode il brief precede il piano e ne è il cappello.
- Se l'obiettivo cambia a lavoro iniziato, correggi il brief con una riga, senza riemetterlo per intero.
- Italiano, come il resto della config.

## Importante

- **Il brief c'è sempre**: prompt e brief si mostrano prima di qualunque altro lavoro, anche per una richiesta breve. Per una richiesta piccola bastano tre righe. Il prompt serve a far vedere subito se la richiesta è stata capita: un brief che la persona non riconduce alla sua richiesta la fa reagire a una ricostruzione invece che alla cosa.
- Se l'arricchimento fa emergere un fatto che cambia le carte (lavoro già fatto, decisione già chiusa in senso opposto, regola del CLAUDE.md che scatta), dillo nel brief prima di procedere: è il motivo principale per cui questa modalità esiste.
- Il brief non è un gate e non richiede conferma: se il prompt è corretto e non hai nulla da chiarire, mostri e procedi. Ma se una domanda di approfondimento cambierebbe materialmente il lavoro, si chiede PRIMA, non dopo aver iniziato.
- **Questa skill si carica col tool `Skill` una volta per sessione**, e di nuovo dopo ogni compattazione: il corpo si legge, non si ricostruisce a memoria da una riga del `CLAUDE.md`. Finché il corpo è nel contesto, una richiesta nuova lo applica senza ricaricarlo: ogni caricamento rimette nel contesto una copia intera (segnalazione n. 17, 27/10/2026). L'hook `inject-now.sh` lo ricorda sui messaggi che non sono comandi.

## MODALITÀ PROMPT ESTERNO — un prompt per un altro tool AI

Si attiva solo quando la persona chiede esplicitamente un prompt da incollare in un altro tool (ChatGPT, Gemini, Cursor, Midjourney, Sora, ElevenLabs, Codex, agenti di coding). Prima di scrivere il prompt leggi per intero `references/prompt-esterno.md` in questa skill: identità, regole, instradamento per tool, diagnostica e formato d'uscita stanno lì. Sta fuori da questo file perché questo file si carica a ogni brief interno, e la modalità esterna serve di rado.
