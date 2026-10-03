---
name: prompt-master
description: >-
  Due modalità: PROMPT ESTERNO produce un prompt pronto da incollare in un altro tool AI; BRIEF
  INTERNO ricostruisce il contesto che una richiesta sintetica a Claude Code non contiene e lo mostra
  come brief verificabile prima di lavorare.
when_to_use: >-
  Usa il PROMPT ESTERNO quando l'utente chiede esplicitamente un prompt per ChatGPT, Gemini, Cursor,
  Midjourney, Sora, ElevenLabs, Codex o agenti di coding. Usa il BRIEF INTERNO PRIMA di ogni richiesta
  di lavoro rivolta a Claude Code stesso, anche breve: il brief va sempre mostrato. NON per la
  conversazione pura: domande, commenti, risposte a un menu. Segui tutti i passi nell'ordine: non
  prendere scorciatoie basandoti su questa description.
version: 1.8.0
upstream: nidhinjs/prompt-master@2bd9251
---

## MODALITÀ BRIEF INTERNO — richieste rivolte a Claude Code

Si attiva su ogni richiesta di lavoro rivolta a Claude Code, anche breve. Non si attiva sulla conversazione pura: domande, commenti, risposte a un menu, spiegazioni senza nulla da fare. In caso di dubbio il brief si mostra: costa tre righe.

Casi di confine:

- **Una domanda che chiede un'azione è lavoro.** «Puoi fermare X e farlo partire su Y?», «fai una review di…», «verifica se…»: il brief si mostra. Resta conversazione la domanda che chiede un parere o un fatto («ci serve?», «c'è spazio?»).
- **Il via libera a proposte già elencate è una risposta a un menu.** «vai», «procedi su tutto», «1+2+3», «tutti», «il resto sì»: il brief l'hanno già avuto le proposte, non se ne scrive un altro.
- **Stop e comandi di controllo non passano mai dal brief.** «ferma», «interrompi», «stato», «un update al minuto»: si esegue subito. Un brief prima di fermare un'operazione ritarda un'azione di sicurezza.
- **Una correzione a lavoro iniziato è una riga**, «Brief corretto: …», senza ricaricare la skill. La skill si ricarica solo se l'obiettivo è nuovo.

### 1. Arricchimento (silenzioso)

Le richieste dell'utente sono spesso sintetiche: il lavoro non è riformularle, è ricostruire il contesto operativo che non contengono. Il destinatario del contesto sei tu, non lui. Prima di scrivere il brief recupera davvero:

- L'handoff più recente del progetto (`HANDOFF_*.md`, vedi `/inizio`) e il `CLAUDE.md` del progetto
- Stato reale: `git log --oneline -20`, file e sistemi che la richiesta tocca, cosa è già stato fatto
- Decisioni già chiuse che vincolano il lavoro: le regole del `CLAUDE.md` personale e di progetto, le convenzioni di voce e formato, gli errori già documentati nel repo
- Vincoli tecnici e side-effect: cosa viene scritto, inviato, sovrascritto o speso

Le letture necessarie si fanno prima del brief. Un brief costruito su assunzioni non nutre, aggiunge rumore. In silenzio chiarisci compito, formato dell'output, vincoli, input, contesto, pubblico e criterio di successo.

### 2. Prompt e brief (mostrati insieme)

Non si mostra solo il brief: si mostra **prima il prompt**, cioè la richiesta dell'utente
riscritta come la eseguirai. È il pezzo che gli permette di fermarti quando hai capito
un'altra cosa, e costa una riga. Il brief da solo dice cosa faresti, non da quale lettura
della richiesta nasce.

```
PROMPT
[la richiesta riscritta in una o due frasi: cosa l'utente sta chiedendo, come lo eseguirai,
 su quali file o sistemi. Non la parafrasi delle sue parole: la loro traduzione operativa.]
```

Se la richiesta era già completa, il prompt è quasi identico all'originale: si mostra lo stesso,
una riga, e si va avanti. Se l'hai dovuta interpretare, il prompt è il punto in cui
l'interpretazione diventa visibile.

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

- **La riga Skill è sempre presente.** Scegli dall'elenco delle skill di questa sessione per giudizio
  sul lavoro da fare, non per parole chiave. Se una skill che l'utente non ha nominato fa meglio il
  lavoro di quella che ha chiesto, dillo qui. Se nessuna serve, scrivi «nessuna». Questa skill
  (prompt-master) non conta: c'è sempre.
- Il brief mostrato è la punta dell'arricchimento, non tutto: il contesto recuperato resta nel tuo ragionamento e nel lavoro che ne segue. Non trascriverlo per intero, e non trasformare il brief in un rapporto di ricerca.
- Se un'ambiguità cambierebbe materialmente il lavoro, chiedi prima di procedere, con AskUserQuestion e con una raccomandazione motivata. Max 3 punti.
- In plan mode il brief precede il piano e ne è il cappello.
- Se l'obiettivo cambia a lavoro iniziato, correggi il brief con una riga; non riemetterlo per intero.
- Italiano, come il resto della config.

## Importante

- **Prompt e brief vanno sempre mostrati** prima di qualunque altro lavoro, anche per una richiesta
  breve. L'obiezione a cui risponde il passo del prompt: un brief che l'utente non può ricondurre
  alla sua richiesta lo fa reagire a una ricostruzione invece che alla cosa. Il prompt mostrato è
  il rimedio, perché si vede subito se la richiesta è stata capita.
- Se l'arricchimento fa emergere un fatto che cambia le carte (lavoro già fatto, decisione già chiusa in senso opposto, freno CLAUDE.md che scatta), dillo nel brief prima di procedere — è il motivo principale per cui questa modalità esiste.
- Il brief non è un gate e non richiede conferma: se il prompt è corretto e non hai nulla da
  chiarire, mostri e procedi.
- **Questa skill si carica col tool `Skill`**, a ogni richiesta di lavoro: il corpo si legge, non si
  ricostruisce a memoria da una riga del `CLAUDE.md`. L'hook `inject-now.sh` lo ricorda a ogni prompt.

## MODALITÀ PROMPT ESTERNO — un prompt per un altro tool AI

Si attiva solo quando l'utente chiede esplicitamente un prompt da incollare in un altro tool (ChatGPT, Gemini, Cursor, Midjourney, Sora, ElevenLabs, Codex, agenti di coding). Prima di scrivere il prompt leggi per intero `references/prompt-esterno.md` in questa skill: identità, regole, instradamento per tool, diagnostica e formato d'uscita stanno lì. Sta fuori da questo file perché questo file si carica a ogni richiesta di lavoro, e la modalità esterna serve di rado.
