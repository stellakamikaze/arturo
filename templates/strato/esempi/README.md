# Esempi da adattare

Questa cartella contiene tre esempi per lo strato di {{ORGANIZZAZIONE}}. Claude Code **non li
carica**: stanno fuori da `plugins/strato/`. Sono un punto di partenza, non regole pronte.

| Esempio | Che cosa mostra |
|---|---|
| `posta/` | Una skill per le email: bozza, confronto con l'email inviata, regola di voce nuova. |
| `recap/` | Una skill per le riunioni: si legge la trascrizione intera, non il riassunto automatico. |
| `anteprima-invio/` | Un hook che mostra destinatari e controlli prima di un invio. Le regole stanno in un file dello strato, non nel codice. |

## Come si adotta un esempio

1. Copia la cartella dell'esempio in `plugins/strato/skills/<nome>/`. Per l'anteprima segui il
   suo `LEGGIMI.md`: è un hook, non una skill.
2. Riscrivi le parti tra parentesi quadre con i vostri strumenti, le vostre cartelle e le vostre
   parole.
3. Togli la riga `disable-model-invocation: true` dal `SKILL.md`. Finché c'è, Claude non usa la
   skill da solo.
4. Provala su un caso vero con `claude --plugin-dir plugins/strato`, poi pubblica con
   `/strato pubblica`.

Gli esempi nominano strumenti generici («lo strumento di posta», «la cartella delle
trascrizioni»). Non nominano persone, account o indirizzi: quelli li scrivi tu, solo nello strato.
