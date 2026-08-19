# Novità

Questo file è il canale di aggiornamento di Arturo. Ogni volta che l'harness evolve in un
modo che vale la pena raccontare, qui compare una entry: cosa cambia, il principio dietro,
a chi serve. La entry più recente sta in cima, con data ISO nell'intestazione.

Non serve leggerlo a mano: dopo un `git pull`, all'avvio della sessione Arturo ti avvisa se
c'è qualcosa che non hai ancora visto, e `/novita` te lo racconta in parole semplici —
con la possibilità di fare sparring (`/sparring`) per capire se la novità serve al tuo
modo di lavorare.

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
