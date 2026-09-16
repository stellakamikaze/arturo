---
name: Arturo
description: Il custode di Claude Code per chi parte da zero, spiegato come un manuale d'uso illustrato.
colors:
  rosso: "#d5301f"
  rosso-scuro: "#a6200f"
  ottanio: "#0d4f5c"
  ottanio-chiaro: "#cfe3e2"
  zinco: "#f3c21b"
  carta: "#e4e1da"
  carta-scura: "#d3cfc6"
  inchiostro: "#141414"
  inchiostro-2: "#3a3935"
  bianco: "#ffffff"
typography:
  display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(4.2rem, 2rem + 9vw, 6rem)"
    fontWeight: 900
    lineHeight: 0.86
    letterSpacing: "-0.035em"
    fontVariation: "'wdth' 125"
  headline:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(2.4rem, 1.4rem + 4vw, 5rem)"
    fontWeight: 800
    lineHeight: 0.98
    letterSpacing: "-0.02em"
    fontVariation: "'wdth' 112"
  title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(1.45rem, 1.1rem + 1vw, 2rem)"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.02em"
    fontVariation: "'wdth' 100"
  cifra:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(4rem, 3rem + 3vw, 6rem)"
    fontWeight: 900
    lineHeight: 0.8
    letterSpacing: "-0.04em"
    fontFeature: "'tnum'"
    fontVariation: "'wdth' 125"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(17px, 1.05rem + 0.15vw, 19px)"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "'tnum'"
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 400
    lineHeight: 1.55
  esito:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 800
    fontVariation: "'wdth' 112"
  mono:
    fontFamily: "ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "0.92em"
rounded:
  none: "0"
spacing:
  gutter: "clamp(16px, 4vw, 48px)"
  colonna: "1240px"
  ritmo: "clamp(72px, 10vw, 144px)"
  testa-sezione: "clamp(40px, 6vw, 72px)"
  passo: "clamp(16px, 2.4vw, 32px)"
  caso: "clamp(24px, 3vw, 40px)"
components:
  bottone:
    backgroundColor: "{colors.zinco}"
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.none}"
    padding: "0 22px"
    height: "52px"
  bottone-vuoto:
    backgroundColor: "transparent"
    textColor: "{colors.bianco}"
    rounded: "{rounded.none}"
    padding: "0 22px"
    height: "52px"
  bottone-vuoto-hover:
    backgroundColor: "{colors.bianco}"
    textColor: "{colors.rosso-scuro}"
  comando:
    backgroundColor: "{colors.carta}"
    textColor: "{colors.inchiostro}"
    typography: "{typography.mono}"
    rounded: "{rounded.none}"
    padding: "12px 14px"
  copia:
    backgroundColor: "{colors.inchiostro}"
    textColor: "{colors.carta}"
    rounded: "{rounded.none}"
    padding: "0 14px"
    width: "88px"
  copia-hover:
    backgroundColor: "{colors.rosso-scuro}"
    textColor: "{colors.bianco}"
  copia-fatto:
    backgroundColor: "{colors.ottanio}"
    textColor: "{colors.carta}"
  esito-blocca:
    backgroundColor: "{colors.rosso}"
    textColor: "{colors.bianco}"
    typography: "{typography.esito}"
    padding: "3px 10px"
  esito-chiede:
    backgroundColor: "{colors.zinco}"
    textColor: "{colors.inchiostro}"
    typography: "{typography.esito}"
    padding: "3px 10px"
  esito-passa:
    backgroundColor: "transparent"
    textColor: "{colors.inchiostro}"
    typography: "{typography.esito}"
    padding: "3px 10px"
  indice-link:
    textColor: "{colors.inchiostro}"
    padding: "6px 0"
  indice-github:
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.none}"
    padding: "6px 12px"
  indice-github-hover:
    backgroundColor: "{colors.inchiostro}"
    textColor: "{colors.carta}"
  caso:
    backgroundColor: "{colors.carta}"
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.none}"
    padding: "{spacing.caso}"
  caso-zinco:
    backgroundColor: "{colors.zinco}"
    textColor: "{colors.inchiostro}"
  caso-ottanio:
    backgroundColor: "{colors.ottanio}"
    textColor: "{colors.bianco}"
  tavola:
    backgroundColor: "{colors.carta-scura}"
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.none}"
---

# Design System: Arturo

## Overview

**Creative North Star: "Il manuale d'uso illustrato"**

Arturo si presenta come le industrie italiane presentavano la macchina da scrivere a chi non l'aveva mai toccata. La pagina è un libretto di istruzioni: tavole numerate, campiture piene, filetti neri spessi, figure geometriche. Il lettore non programma, quindi il sistema mostra un oggetto da montare e non un prodotto software.

La densità è media e ordinata. Ogni sezione è una campitura a tutta larghezza: rosso segnale, giallo zinco, carta, carta scura, blu ottanio, di nuovo rosso, e il piede in inchiostro. Una griglia a 12 colonne divide lo spazio in proporzioni asimmetriche (7/5, 5/7, 4/1/7). Un solo grottesco, Archivo, porta tutta la voce: la larghezza variabile distingue il titolo dal testo, non un secondo carattere.

Il contratto di direzione rifiuta due cose, e la build le rispetta: l'hero scuro con il terminale al neon e le card a gradiente.

**Key Characteristics:**
- Campiture piene di tre colori segnale su carta grigio-calda.
- Filetti neri da 3px come unica struttura, angoli sempre retti.
- Tavole numerate («Tav. 1», «Tav. 2») con didascalia a bandiera sotto un filetto.
- Il custode geometrico: un solo simbolo fatto di cerchio, trapezio e triangoli.
- Un solo grottesco a larghezza variabile, con cifre tabellari in tutta la pagina.
- Nessuna ombra, nessun gradiente, nessun raggio.

## Colors

Tre colori segnale a piena saturazione su una carta grigio-calda, con l'inchiostro quasi nero come unico colore di linea.

### Primary
- **Rosso segnale**: il colore del marchio e delle due campiture che aprono e chiudono la pagina. Colora la stella del custode, il papillon, l'esito «Blocca» e i numeri grandi degli Impegni. Sul rosso il testo è bianco (contrasto 4,92:1).
- **Rosso bruciato** (rosso-scuro): il rosso per il testo piccolo su carta. Colora i nomi dei comandi nelle liste e negli schemi (5,67:1 su carta) e l'hover del tasto «Copia» e del bottone vuoto.

### Secondary
- **Blu ottanio**: la campitura dei limiti onesti («Cosa non è neutro») e del caso «Chi insegna o vuole imparare». Sul blu il testo è bianco (9,17:1) e i comandi e le icone sono in giallo zinco (5,48:1). Segna anche lo stato «Copiato».
- **Ottanio chiaro**: il fondo delle tavole dentro i casi su ottanio e della tavola grande del primo caso.

### Tertiary
- **Giallo zinco**: la campitura delle Istruzioni di montaggio, il bottone principale, l'esito «Chiede a te», la selezione del testo, il link «Vai al contenuto». Porta sempre testo in inchiostro (11:1).

### Neutral
- **Carta grigio-calda** (carta): il fondo della pagina, dei casi, dei campi comando e dei blocchi dello schema.
- **Carta scura**: il fondo delle tavole illustrate e della sezione «Come protegge la casa».
- **Inchiostro**: il testo, tutti i filetti, il corpo del custode, il tasto «Copia», il piede.
- **Inchiostro medio** (inchiostro-2): il testo di accompagnamento sotto i titoli di sezione e nelle liste (8,85:1 su carta).
- **Bianco**: il testo e i filetti sulle campiture rosse e ottanio. Nel CSS è scritto come `#fff` letterale.

### Named Rules
**La Regola della Campitura Piena.** Il colore occupa una superficie intera, delimitata da un filetto nero. Non esistono sfumature, trasparenze decorative o gradienti. L'unica trasparenza è il filetto sottile tra le righe di una lista (inchiostro o bianco al 30-35%).

**La Regola del Rosso Grande.** Il rosso segnale diventa testo solo a dimensione display, come i numeri degli Impegni (su carta il contrasto è 3,76:1). Per il testo piccolo usa il rosso bruciato.

## Typography

**Display Font:** Archivo variabile, larghezza 62-125%, pesi 100-900 (con system-ui, sans-serif)
**Body Font:** Archivo, la stessa famiglia
**Label/Mono Font:** ui-monospace di sistema (SF Mono, Menlo, Consolas) solo per comandi e percorsi

**Character:** Un grottesco industriale che cambia voce allargandosi. Il titolo è largo e pesante come una targa, il testo resta a larghezza normale e leggibile. Il font sta nel repository in `sito/font/`, con licenza OFL.

### Hierarchy
- **Display**: il nome «Arturo» nella campitura rossa, larghissimo e compresso in altezza. Il sottotitolo nello stesso `h1` scende a 0,42em, peso 700, larghezza 100%.
- **Headline**: i titoli di sezione («Istruzioni di montaggio», «Impegni»), larghezza 112%, 125% nella chiusura.
- **Title**: i titoli dei passi, dei casi e delle avvertenze, massimo 18 caratteri di misura nei casi.
- **Cifra**: i numeri dei passi di montaggio, peso 900 a larghezza piena. I numeri degli Impegni usano la stessa voce a 2,6rem.
- **Body**: il testo corrente, misura massima 64ch, cifre tabellari ovunque.
- **Label**: le didascalie delle tavole. «Tav. N» è in grassetto a larghezza 125%, il testo segue a bandiera.
- **Esito**: le etichette «Blocca», «Chiede a te», «Passa» dello schema delle guardie.

### Named Rules
**La Regola del Solo Grottesco.** Tutta la pagina usa Archivo. La gerarchia nasce da peso e larghezza (100%, 110%, 112%, 125%), mai da un secondo carattere. Il monospace serve solo al codice.

**La Regola dei Font di Casa.** I font si servono dalla stessa cartella del sito. Nessun font da server esterni.

## Layout

Una colonna centrale larga fino a 1240px, con margini laterali da 16px a 48px. Ogni sezione è una fascia a tutta larghezza con padding verticale `ritmo` (da 72px a 144px). Le fasce si separano con un filetto da 3px.

Dentro la colonna vale una griglia modernista a 12 colonne, espressa con proporzioni asimmetriche:
- Apertura e chiusura: 7/5. A sinistra la campitura con il titolo, a destra la tavola.
- Testata di sezione: 6/6, titolo a sinistra e testo a destra.
- Casi d'uso: griglia a 12 colonne con filetti su ogni cella. Un caso pieno (12, diviso 5/7), una coppia 7+5, un caso pieno (12, diviso 7/5).
- Istruzioni di montaggio e avvertenze: tre colonne uguali divise da filetti verticali da 2px.
- Impegni: 5/7. Schema delle guardie: 4/1/7, con la freccia nella colonna stretta.

La testata resta fissa in alto (altezza minima 64px). Sotto 900px ogni griglia diventa una colonna sola e i filetti verticali diventano orizzontali. Sotto 860px l'indice mostra solo il link GitHub. Sotto 520px le liste di comandi mettono la descrizione sotto il comando.

**La Regola dell'Asimmetria.** Due colonne affiancate non sono mai uguali, tranne nella testata di sezione. Il peso visivo sta a sinistra (7 o 5 contro 5 o 7).

## Elevation & Depth

Il sistema è piatto. Non esistono ombre. La profondità nasce dalla sovrapposizione di campiture e dai filetti neri, come in una tavola stampata. L'unico movimento in profondità è lo spostamento di 2px verso l'alto del bottone in hover, e 1px verso il basso alla pressione.

**La Regola della Stampa Piatta.** Nessuna ombra, nessun gradiente, nessun blur. Un elemento si stacca dal fondo con un filetto o con una campitura diversa.

## Shapes

Tutti gli angoli sono retti (raggio 0). La forma sta nei filetti: 3px per la struttura (testata, sezioni, casi, bottoni, blocchi), 2px per le divisioni interne (passi, didascalie, campo comando, tasto GitHub), 1px al 30-35% di opacità tra le righe delle liste.

Le illustrazioni usano solo primitive geometriche: cerchi, rettangoli, trapezi, triangoli, la stella a cinque punte. I tratti sono da 4-5px in inchiostro. Le frecce dello schema sono un filetto da 3px con una punta disegnata dai bordi CSS. Le icone delle avvertenze sono disegni SVG a tratto da 4px in giallo zinco.

**La Regola del Filetto.** Un confine si disegna in inchiostro pieno, spesso e dritto. Mai bordi grigi sottili come unica separazione tra due campiture.

## Components

### Buttons
Un tasto meccanico: pieno, squadrato, bordato di nero.
- **Shape:** angoli retti, bordo in inchiostro da 3px, altezza minima 52px.
- **Principale** (bottone): fondo giallo zinco, testo inchiostro, peso 700, larghezza 110%, icona SVG a 18px dopo il testo.
- **Vuoto** (bottone-vuoto): sulle campiture rosse. Fondo trasparente, testo e bordo bianchi. In hover il fondo diventa bianco e il testo rosso bruciato.
- **Hover / Focus:** sale di 2px in 180ms con curva `cubic-bezier(.16,1,.3,1)`, scende di 1px alla pressione. Il focus è un contorno da 3px in inchiostro a 3px di distanza, giallo zinco sulle campiture rosse e ottanio.

### Campo comando
Il comando da copiare, come una targhetta avvitata.
- **Style:** fondo carta, bordo inchiostro da 2px, testo monospace a 0,85rem che va a capo sulle barre dell'URL.
- **Tasto Copia:** blocco inchiostro attaccato a destra, larghezza minima 88px, testo carta in grassetto. Hover rosso bruciato. Dopo la copia diventa ottanio e dice «Copiato» per 2 secondi. Se il browser non permette la copia, seleziona il testo e dice di premere Cmd o Ctrl+C.

### Chips (esiti delle guardie)
- **Style:** etichette squadrate, peso 800, larghezza 112%, padding 3px 10px.
- **Varianti:** «Blocca» su rosso con testo bianco, «Chiede a te» su zinco con testo inchiostro, «Passa» senza fondo con bordo inchiostro da 2px.

### Cards / Containers (casi d'uso)
- **Corner Style:** angoli retti.
- **Background:** carta, oppure campitura zinco o ottanio per alternare i casi.
- **Shadow Strategy:** nessuna ombra (vedi Elevation & Depth).
- **Border:** filetto inchiostro da 3px a destra e sotto, la griglia porta quello in alto e a sinistra.
- **Internal Padding:** `caso`, da 24px a 40px.
- **Contenuto:** titolo, testo, lista di comandi e una tavola illustrata. La lista mette il comando in monospace rosso bruciato (zinco sull'ottanio) accanto alla descrizione, righe divise da filetti sottili.

### Navigation
- **Style:** testata fissa su carta, filetto inchiostro da 3px sotto. A sinistra il marchio (quadrato rosso con stella zinco, 28px) e «Arturo» in peso 800 a larghezza 125%.
- **Link:** peso 600, 0,95rem, senza sottolineatura. In hover compare un filetto rosso da 2px sotto.
- **GitHub:** l'ultimo link è un riquadro bordato di inchiostro da 2px, pieno di inchiostro in hover.
- **Mobile:** sotto 860px resta solo GitHub.

### Tavola illustrata
Il componente che definisce il sistema.
- Una figura su carta scura (ottanio chiaro nei casi su ottanio), con bordo inchiostro e la didascalia sotto un filetto da 2px.
- La didascalia comincia con «Tav. N» in grassetto largo, poi una frase a bandiera che descrive la scena.
- Il custode è un unico simbolo SVG riusato: testa a cerchio, marsina a trapezio, sparato triangolare in carta, papillon rosso. Ogni scena cambia gli oggetti intorno a lui (il tasto `/setup`, il terminale, i fogli, i computer, la lavagna).
- Nella tavola d'apertura i pezzi del custode si montano in sequenza (900ms, 90ms di scarto tra un pezzo e l'altro) e la stella si accende ruotando. È l'unica animazione della pagina e si spegne con `prefers-reduced-motion`.

### Passi di montaggio
- Tre colonne sulla campitura zinco, sotto un filetto da 3px. Ogni passo ha la cifra enorme, il titolo, il testo e, dove serve, il campo comando.

### Impegni
- Lista numerata: la cifra rossa a 2,6rem in una colonna da 64px, poi l'impegno in grassetto e la spiegazione in inchiostro medio. Righe divise da filetti da 2px.

## Do's and Don'ts

### Do:
- **Do** separa ogni fascia e ogni cella con un filetto inchiostro da 3px (2px per le divisioni interne).
- **Do** dai a ogni illustrazione il suo numero di tavola e una didascalia a bandiera che descrive la scena.
- **Do** costruisci ogni figura con il simbolo unico del custode e con primitive geometriche a tratto da 4-5px.
- **Do** metti i comandi in un campo comando con il tasto Copia, e i nomi dei comandi in monospace rosso bruciato.
- **Do** usa testo bianco su rosso e ottanio, testo inchiostro su zinco e carta.
- **Do** tieni un'animazione sola per pagina, legata al montaggio del custode, e spegnila con `prefers-reduced-motion`.

### Don't:
- **Don't** arrotondare gli angoli: il raggio è sempre 0.
- **Don't** usare ombre, gradienti, blur o l'hero scuro con il terminale al neon.
- **Don't** aggiungere un secondo carattere di testo: la gerarchia la fanno peso e larghezza di Archivo.
- **Don't** usare il rosso segnale per testo sotto la dimensione display.
- **Don't** caricare font, script o immagini da server esterni.
