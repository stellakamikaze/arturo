# Regole di interfaccia

Controlla ogni interfaccia costruita contro queste regole, prima di dire "fatto". Il file non è una direzione di design: copre ciò che Impeccable e Hallmark non dicono, o non portano su quella superficie.

## Chi vince e cosa leggi

Precedenza: il brief e il `DESIGN.md` del progetto, poi Impeccable e Hallmark, poi questo file. Se una regola di default va contro una di loro, vince la loro. Una regola fissa cede solo a una scelta esplicita della persona, e tu la riporti.

```
pagina costruita da Hallmark            --> Parte A
dashboard, tool, app, rifinitura        --> Parte A e Parte B
Impeccable non installata               --> Parte A, B e C
```

Le regole "fissa" sono errori oggettivi o requisiti di accessibilità. Le regole "default" sono punti di partenza: rompile quando il design lo chiede, e dillo. Riporta ogni problema con la schermata e l'elemento. Tieni separati i difetti misurabili dalle scelte che spettano alla persona.

## Parte A: ciò che manca a tutte e due

### Dati e grafici

- (fissa) Ogni grafico ha un'alternativa testuale: una descrizione dell'andamento o una tabella accessibile. [WCAG 1.1.1, AF]
- (fissa) Linee e barre hanno contrasto 3:1 con lo sfondo, e i segmenti vicini 3:1 fra loro o un bordo. L'obbligo cade se ogni valore è stampato. [WCAG 1.4.11]
- (fissa) Un dato mancante spezza la linea: i punti ai due lati non si uniscono, nemmeno col tratteggio. [AF]
- (fissa) I piccoli multipli con la stessa unità usano la stessa scala sull'asse y. [AF]
- (fissa) I numeri in tabella stanno a destra, con l'intestazione allineata come loro. [Post, AF-T]
- (default) Una colonna di numeri ha la stessa precisione su ogni riga, e l'unità sta nell'intestazione. [AF-T]
- (default) Un numero che cambia nel tempo dice il periodo e la variazione: "+8,1% su settembre". [Post]
- (default) Sulle linee metti il nome a fine linea, senza legenda. [AF, DW]
- (default) Il titolo del grafico dice il messaggio, il sottotitolo dice cosa, dove e quando, e la fonte ha un link. Titolo e sottotitolo stanno in HTML, fuori dall'immagine. [AF, DW]
- (default) Massimo quattro linee, quattro categorie per pila, quattro barre per gruppo. Oltre, usa piccoli multipli o una tabella. [AF]
- (default) Il testo dei grafici resta orizzontale. Se non entra, usa barre orizzontali o accorcia. [AF, DW]

### Form

- (fissa) Cambiare un select, un radio o una casella non naviga e non invia il form. [WCAG 3.2.2]
- (fissa) Un dato già inserito in un flusso a più passi è precompilato o selezionabile. [WCAG 3.3.7]
- (fissa) Il codice di verifica si incolla intero, anche con una casella per cifra, e nessuno script blocca il gestore di password. [WCAG 3.3.8]
- (fissa) Invio invia il campo attivo. In una textarea invia Cmd o Ctrl+Invio. [VWG]
- (fissa) Con modifiche non salvate, l'uscita dalla pagina o dal pannello mostra un avviso. [VWG]
- (fissa) Etichetta e controllo di checkbox e radio sono un solo bersaglio, senza zone morte. [VWG]
- (fissa) Niente autofocus al caricamento sui dispositivi touch: apre la tastiera e copre lo schermo. [RAUNO]
- (fissa) Un `<select>` nativo ha `background-color` e `color` espliciti: su Windows in tema scuro le opzioni diventano illeggibili. [VWG]
- (default) Dopo un invio fallito, in cima alla pagina compare un riepilogo degli errori, con un link a ogni campo. [GOV]
- (default) Un form sta su una colonna. Sulla stessa riga vanno solo campi molto legati, come città e CAP. [BAY]
- (default) Un interruttore ha effetto subito. In un form con bottone Salva usa una casella. [NNG, RAUNO]

### Controlli, overlay e movimento

- (fissa) Ogni trascinamento, swipe o pinch ha un'alternativa a clic singolo. La tastiera da sola non basta. [WCAG 2.5.7, 2.5.1]
- (fissa) Una barra fissa o un banner non nasconde del tutto l'elemento col focus: `scroll-padding` copre l'altezza delle barre. [WCAG 2.4.11]
- (fissa) Alla chiusura di un dialog o di un pannello sovrapposto il focus torna all'elemento che l'ha aperto. [APG]
- (fissa) Modali, drawer e overlay scorrevoli hanno `overscroll-behavior: contain`. [VWG]
- (fissa) Il peso del carattere non cambia su hover o selezione: sposta il layout. [RAUNO]
- (fissa) Il cambio di tema, a mano o dal sistema, non fa partire transizioni né animazioni. [RAUNO]
- (fissa) Una griglia `auto-fit` o `auto-fill` usa `minmax(min(100%, X), 1fr)`: senza `min()` sborda sugli schermi stretti. [SMOL]
- (fissa) Il testo resta intero con la spaziatura forzata: interlinea 1.5, paragrafi 2em, lettere 0.12em, parole 0.16em. [WCAG 1.4.12]
- (fissa) Un passaggio in un'altra lingua porta il suo `lang`. Sono esclusi nomi propri, termini tecnici e prestiti. [WCAG 3.1.2]
- (fissa) Nessun permesso (posizione, notifiche, camera) si chiede al caricamento della pagina. [WEBDEV]
- (default) Le voci vicine di una lista cliccabile non hanno zone morte: lo spazio è padding, non margine. [RAUNO]
- (default) Un'entrata parte da scala 0.9 o più con opacità 0, mai da `scale(0)`. [EMIL]
- (default) Un'attesa oltre 10 secondi mostra la percentuale e un comando per fermare. [NNG-P]

### Testo e spazio

- (fissa) Un link dentro un paragrafo ha colore e sottolineatura: il solo colore non basta. [Post]
- (default) Un testo oltre due righe sta allineato a sinistra, mai centrato. [Post]
- (default) Il padding esterno di un contenitore è uguale o maggiore dello spazio fra i suoi elementi. [HOBDAY]

## Parte B: coperte da Hallmark, ma assenti su dashboard, tool e app

Hallmark carica queste regole solo quando costruisce una pagina. Su una superficie guidata da Impeccable non arrivano, quindi valgono da qui.

- (fissa) Le barre partono da zero, salvo una scala dichiarata nel grafico: "l'asse parte da 94%". [Post]
- (default) Oltre tre parti, usa barre ordinate, non la torta. [Post]
- (default) Evidenzia una serie e metti in grigio le altre. [Post]
- (fissa) Un elemento a ridosso del bordo ha raggio interno uguale al raggio esterno meno il padding. Se il padding supera il raggio, la regola non vale. [Post]
- (fissa) Ogni campo ha il `type` e l'`inputmode` giusti, così si apre la tastiera giusta. [Post]
- (fissa) L'etichetta sta più vicina al suo campo che al campo sopra. [Post]
- (default) Una scheda ha almeno 16px di padding. [Post]
- (default) In tema scuro lo sfondo è grigio molto scuro e il testo off-white: niente nero puro, niente bianco puro. [Post]
- (default) In tema scuro l'accento è più chiaro e meno saturo, e le superfici salgono con grigi più chiari, non con le ombre. [Post]
- (default) In tema scuro un'immagine chiara ha una versione scura o sta in un riquadro. Non usare filtri CSS. [Post]

## Parte C: solo se Impeccable non c'è

Impeccable copre già queste regole. Leggile solo se manca.

- (fissa) Il testo ha contrasto 4.5:1, anche sui bottoni colorati e il testo grigio in tema scuro. [Post]
- (fissa) Un errore ha un messaggio scritto, mai il solo colore. [Post]
- (fissa) Il rosso dice pericolo e il verde dice successo: i significati non cambiano. [Post]
- (fissa) Ogni bersaglio tattile è almeno 44x44. [Post]
- (fissa) Il testo degli input è 16px, altrimenti iPhone ingrandisce al focus. [Post]
- (fissa) Nessuna azione è solo su hover. [Post]
- (fissa) Il bottone dice cosa succede: "Elimina il progetto", non "OK". [Post]
- (fissa) Il placeholder non sostituisce l'etichetta. [Post]
- (default) Gli spazi vengono da una sola scala: 4, 8, 16, 24, 32. [Post]
- (default) Lo spazio fra i gruppi è maggiore dello spazio dentro un gruppo. [Post]
- (default) Tutto si allinea su un bordo solo. [Post]
- (default) Un solo accento, per l'azione principale. Gli altri bottoni restano neutri. [Post]
- (default) Il bottone principale su mobile sta in basso. [Post]
- (default) Su mobile usa un pannello dal basso, non una piccola finestra centrata. [Post]
- (default) Il corpo del testo ha interlinea da 1.4 a 1.6 e righe da 45 a 75 caratteri. [Post]
- (default) I titoli sono chiaramente più grandi o più pesanti del testo. [Post]
- (default) Uno o due caratteri, e varietà col peso. [Post]
- (default) I titoli grandi hanno il tracking stretto. [Post]

## Lasciate fuori

- L'etichetta maiuscola sopra un testo: Impeccable vieta l'eyebrow, in ogni caso.
- Il numero grande con le statistiche sotto: è il modello hero-metric che Impeccable rifiuta. Resta l'ordine di lettura: prima ciò che conta.
- Tinte tenui su ogni area grande: Impeccable ammette una regione di colore deciso.
- Attenuare le immagini in tema scuro: Hallmark vieta i filtri CSS.
- Animare solo `transform` e `opacity`, durate sotto 200 ms, mai `ease-in`, ombre a strati, niente pesi sotto 400: le guide di mestiere dicono così, Impeccable o Hallmark dicono altro.
- Radio preselezionati: GOV.UK e NN/g si contraddicono.

## Fonti

- Post: u/yung_quan, r/ClaudeDesign, "7 UI Do's and Don'ts cheat sheets", novembre 2026. https://www.reddit.com/r/ClaudeDesign/
- WCAG: https://www.w3.org/WAI/WCAG22/Understanding/ (numero del criterio accanto alla regola)
- APG: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
- AF: https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/
- AF-T: https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-tables/
- DW: https://www.datawrapper.de/blog/text-in-data-visualizations
- GOV: https://design-system.service.gov.uk/components/error-summary/
- BAY: https://baymard.com/research-articles/avoid-multi-column-forms
- NNG: https://www.nngroup.com/articles/toggle-switch-guidelines/
- NNG-P: https://www.nngroup.com/articles/progress-indicators/
- WEBDEV: https://web.dev/articles/permissions-best-practices
- VWG: https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/AGENTS.md
- RAUNO: https://interfaces.rauno.me/
- EMIL: https://emilkowal.ski/ui/7-practical-animation-tips
- HOBDAY: https://anthonyhobday.com/sideprojects/saferules/
- SMOL: https://smolcss.dev/#smol-css-grid
