# Checklist di verifica

Esegui questo passaggio su ogni bozza prima di consegnarla. I controlli vanno dal meccanico al giudizio.

## Controlli meccanici (cercabili)

Cerca ogni schema nella bozza. Ogni occorrenza fuori dai blocchi di codice e dal testo citato è una violazione.

| Cerca | Violazione | Correzione |
|---|---|---|
| `ando`, `endo` a inizio frase o dopo virgola | Gerundio con funzione di verbo (Regola 3.3) | Due frasi con soggetto esplicito. |
| `rebbe`, `rebbero`, `resti`, `remmo`, `reste` | Condizionale (Regola 3.2) | Indicativo. Vedi la scala dei modali. |
| `sse`, `ssero`, `qualora`, `laddove`, `nell'eventualità` | Congiuntivo o ipotetica pesante (Regola 3.2) | `Se` più indicativo. |
| `si consiglia`, `è opportuno`, `si raccomanda`, `dovresti` | Modale vietato (Regola 3.9) | `devi`, oppure cancella. |
| `viene eseguito`, `vengono creati`, `è stato configurato` | Passivo evitabile (Regola 3.5) | Voce attiva con soggetto. |
| `si esegue`, `si configura`, `si procede` | "Si" passivante in procedura (Regola 3.6) | Imperativo. |
| `effettuare`, `provvedere a`, `procedere a`, `realizzare la` | Nominalizzazione (Regola 3.7) | Il verbo pieno. |
| `andare a`, `andiamo a`, `vai a` più infinito | Perifrasi verbale (Regola 9.3) | Il verbo da solo. |
| `;` | Punto e virgola (Regola 8.1) | Due frasi. |
| `—` usata come pausa | Lineetta lunga retorica (Regola 8.8) | Punto, virgola o parentesi. |
| `ad es.`, `cfr.`, `N.B.`, `ecc.` | Abbreviazione oscura (Regola 9.5) | "per esempio", "vedi", "Nota", elenca le voci. |
| `semplicemente`, `robusto`, `potente`, `senza soluzione di continuità`, `consente di` | Parola senza fatto | Cancella o sostituisci. |
| `utilizzare`, `al fine di`, `in termini di`, `a livello di` | Burocratese (Regola 1.4) | La parola corta. |
| ` se `, ` quando `, ` qualora ` a metà frase | Condizione in coda (Regola 5.4) | Porta la condizione all'inizio, con la virgola. |
| `perchè`, `poichè`, `affinchè`, `qual'è`, `e'`, `puo'`, `piu'`, `citta'` | Errore di accento (Regole 10.1, 10.2) | Correggi. |
| `ad` non seguito da `a`, `ed` non seguito da `e` | D eufonica sbagliata (Regola 10.3) | `a`, `e`. |

## Controlli numerabili

1. **Lunghezza delle frasi.** Conta le parole di ogni frase. Limite procedurale: 22. Limite descrittivo: 28. Note: 28. Comandi tra backtick, numeri con unità e identificatori valgono una parola ciascuno (Regola 8.6).
2. **Dimensione dei paragrafi.** Massimo sei frasi per paragrafo (Regola 6.6).
3. **Catene di nomi.** Ogni catena oltre le tre parole va spezzata con le preposizioni (Regola 2.1).
4. **Istruzioni per frase.** Una, salvo azioni simultanee (Regola 5.2).
5. **Forma dell'istruzione.** Una sola forma in tutto il documento: imperativo oppure infinito, mai le due insieme (Regola 5.3).

## Controlli di giudizio

6. **Classificazione.** Ogni passaggio è chiaramente procedurale o descrittivo? Le procedure stanno all'imperativo, le descrizioni non ci stanno mai.
7. **Voce.** Per ogni frase passiva: l'agente è davvero ignoto, e il passaggio è descrittivo? Altrimenti rendila attiva (Regola 3.5).
8. **Soggetto.** Dopo due frasi senza soggetto esplicito, il lettore sa ancora chi agisce? (Regola 4.6)
9. **Rotazione di sinonimi.** Un termine per concetto in tutto il documento (Regole 1.11, 9.4). Controlla le serie verifica/controlla/accertati, configurazione/impostazioni/parametri, esegui/avvia/lancia, errore/problema/criticità.
10. **Avvertenze.** Prima il comando o la condizione, poi il rischio. Il livello dichiarato è quello giusto (Regole 7.1-7.3).
11. **Completezza.** Articoli presenti, "che" completivo presente, niente stile telegrafico (Regola 4.2).
12. **Intoccabili intatti.** Codice, identificatori, errori citati, citazioni normative e nomi propri sono invariati.

## Quando riporti le violazioni (modalità controllo)

Per ogni violazione dai: il numero di regola, il testo che viola la regola, una riscrittura conforme. Cita solo i numeri di regola presenti in SKILL.md.

Quando l'utente ha chiesto la conformità, chiudi il report con questa dichiarazione: "ITS è un adattamento italiano non ufficiale di ASD-STE100. ASD-STE100 vale solo per l'inglese e nessuno strumento può garantire la conformità a una lingua controllata. L'ultima parola resta a chi scrive. La norma originale è scaricabile gratis su asd-ste100.org."
