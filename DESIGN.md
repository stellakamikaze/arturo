---
name: Arturo
description: Il custode di Claude Code raccontato come la stella dei naviganti, su una pagina quieta tra scene dipinte.
colors:
  tela: "#fefffc"
  carta: "#ffffff"
  lino: "#f9faf7"
  inchiostro: "#171717"
  grafite: "#2c2c2c"
  carbone: "#444141"
  cenere: "#646464"
  nebbia: "#b4b8b4"
  foschia: "#dee2de"
  crepuscolo: "#282834"
  notte: "#1f1f29"
  sera: "#2b6f9e"
  sera-chiaro: "#8cc4e6"
  mare: "#0d5e8f"
  passa: "#2f7a4f"
  blocca: "#b2392b"
  arturo: "#f2a24a"
typography:
  display:
    fontFamily: "Sorts Mill Goudy, Iowan Old Style, Georgia, serif"
    fontSize: "clamp(2.1rem, 1.5rem + 1.8vw, 3.1rem)"
    fontWeight: 400
    lineHeight: 1.08
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Sorts Mill Goudy, Iowan Old Style, Georgia, serif"
    fontSize: "clamp(2rem, 1.35rem + 1.9vw, 3rem)"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Sorts Mill Goudy, Iowan Old Style, Georgia, serif"
    fontSize: "clamp(1.45rem, 1.25rem + 0.6vw, 1.7rem)"
    fontWeight: 400
    lineHeight: 1.25
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "clamp(16.5px, 0.98rem + 0.15vw, 18px)"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.005em"
  label:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 600
    lineHeight: 1.3
  mono:
    fontFamily: "Atkinson Hyperlegible Mono, ui-monospace, monospace"
    fontSize: "0.86rem"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  bottone: "8px"
  card: "12px"
  contenitore: "16px"
  scena: "24px"
  pillola: "50px"
spacing:
  gutter: "clamp(16px, 4vw, 48px)"
  colonna: "1200px"
  ritmo: "clamp(72px, 9vw, 128px)"
components:
  azione-piena:
    backgroundColor: "{colors.notte}"
    textColor: "{colors.carta}"
    rounded: "{rounded.bottone}"
    padding: "0 16px"
    height: "44px"
  azione-bordo:
    textColor: "{colors.sera}"
    rounded: "{rounded.bottone}"
    padding: "0 16px"
    height: "44px"
  azione-chiara:
    backgroundColor: "{colors.carta}"
    textColor: "{colors.notte}"
    rounded: "{rounded.bottone}"
    padding: "0 16px"
    height: "44px"
  pannello:
    backgroundColor: "{colors.carta}"
    rounded: "{rounded.card}"
    padding: "clamp(22px, 3vw, 32px)"
  comando:
    backgroundColor: "{colors.notte}"
    textColor: "#eef0ec"
    typography: "{typography.mono}"
    rounded: "{rounded.bottone}"
  campo:
    backgroundColor: "{colors.lino}"
    textColor: "{colors.grafite}"
    rounded: "0px"
    height: "46px"
---

# Design System: Arturo

## Overview

**North Star: «La stella dei naviganti».** Arturo viene da Arktouros, il guardiano dell'orsa: la stella che segue l'Orsa Maggiore e che i naviganti usavano per non perdere la rotta. La pagina lo racconta con scene dipinte del cielo d'Italia all'ora blu, in cui Arturo è sempre il punto più luminoso e l'unico calore arancio. Tra una scena e l'altra l'interfaccia è quieta: bianco caldo, filetti verde-grigio, un serif da libro a peso 400.

Il registro viene dal riferimento Refero «General Intelligence Company» scelto da Federico il 1/10/2026: le illustrazioni fanno il lavoro emotivo, la UI sussurra. Sostituisce il mondo dell'archivio d'ufficio del 30/9.

Rifiuta l'hero scuro col terminale, la griglia di card uguali, le maiuscole urlate.

## Colors

Strategia: **ristretta**. Neutri caldi più un solo accento blu sera. Il colore saturo vive solo nei dipinti e in un'unica superficie piena, il blu mare di «Cosa non è neutro».

### Primary
- **Sera** (`#2b6f9e`): l'unico accento della UI. Bordo delle azioni secondarie, stato selezionato, numeri delle sequenze vere. Contrasto 5,4:1 su bianco.

### Neutral
- **Tela** (`#fefffc`) è il fondo della pagina. **Carta** (`#ffffff`) è il fondo di card e sezioni alternate. **Lino** (`#f9faf7`) è il fondo di prove, campi e chip.
- **Grafite** per titoli, **carbone** per il testo, **cenere** per il testo secondario e le etichette (5,9:1 su bianco). **Foschia** per i filetti, **nebbia** per le cornici dello schema degli strati.
- **Notte** e **crepuscolo**: l'unico pieno scuro della UI (azione principale, blocchi comando).

### Named Rules
**La Regola della Stella.** L'arancio di Arturo (`#f2a24a`) compare solo come stella: nei dipinti, nel marchio e nel punto accanto alla data. Mai su testo, bottoni o fondi.
**La Regola degli Esiti.** Gli esiti delle guardie hanno tre colori fissi: sera «Chiede a te», verde `#2f7a4f` «Passa», rosso `#b2392b` «Blocca». Sempre come bordo e testo, mai come fondo pieno.

## Typography

- **Sorts Mill Goudy** (400, tondo e corsivo): titoli, sottotitoli di card, citazioni, numeri delle sequenze. Mai in grassetto: la voce è bassa. Cifre maiuscole (`lining-nums`) nei numeri, perché l'«1» in stile antico si legge come una «I».
- **Atkinson Hyperlegible Next**: tutto il resto. Scelto per la leggibilità di chi non è tecnico. Etichette a 600, testo a 400, mai sotto 12 px.
- **Atkinson Hyperlegible Mono**: solo comandi, percorsi e messaggi veri delle guardie. Lo zero barrato è il disegno del font.
- Nel CSS le famiglie si chiamano «Sorts Mill Goudy», «Atkinson Next» e «Atkinson Mono». Tutti OFL, ospitati in `sito/font/`.

### Hierarchy
Display (titolo d'apertura, tre righe al massimo) → headline di sezione → title di card → body → label. Ogni passo cambia misura e famiglia, non peso.

### Named Rules
**Cifre tabulari solo nelle tabelle.** Il registro delle guardie e la tabella dello strato le usano, il testo corrente no.

## Layout

Colonna di 1200 px con gutter fluido, ritmo verticale di 72–128 px tra le sezioni. Le sezioni si alternano su tela e carta, separate da un filetto. Testate a due colonne: titolo a sinistra (7/12), attacco a destra (5/12) allineato in basso. Sotto 820–900 px tutto va a una colonna, sempre con `minmax(0,1fr)`: una colonna `1fr` si allarga per far stare un comando lungo e la pagina sborda.

## Elevation & Depth

Profondità leggera e reale, mai alone. Card: `0 1px 1px` più `0 4px 5px` al 8%. Scene: un anello di 5 px quasi invisibile. Il vetro smerigliato (`backdrop-filter: blur(22px)`) esiste solo sopra i dipinti.

## Shapes

Raggi fissi: 8 px bottoni e comandi, 12 px card e strati, 16 px contenitori, 24 px scene e vetri, pillola solo per la navigazione e gli esiti. Il campo password ha angoli vivi e solo il filetto in basso, come un modulo cartaceo.

## Components

### Navigazione a pillola
Fissa in alto al centro. Trasparente e smerigliata sopra la scena d'apertura, diventa tela all'80% sul bianco. Marchio (colline e stella), quattro voci, azione «Installa». Sotto 760 px restano marchio e azione.

### Vetro sulla scena
Card smerigliata con titolo serif bianco sopra un dipinto. Nell'apertura entra una volta sola (dissolvenza, salita di 14 px, sfocatura che si toglie) mentre la scena si posa. Su mobile la scena sta sopra e il vetro sotto, sovrapposto di 96 px, così il soggetto del dipinto resta visibile.

### Strati annidati (componente firma)
Quattro cornici una dentro l'altra (Claude Code › Arturo › Lo strato › Tu) che sono anche un `tablist` verticale con frecce, Home e End. Lo strato scelto prende il bordo sera e un velo azzurro. Sopra i 900 px lo schema resta fisso mentre il pannello scorre.

### Registro delle guardie
Lista numerata: comando in mono grassetto, nota, messaggio vero della guardia su lino, nome della guardia, pillola d'esito. Su mobile la guardia e l'esito scendono sotto il messaggio.

### Comandi da copiare
Blocco notte con pulsante «Copia» a destra. Il testo va a capo per intero (`pre-wrap`, `overflow-wrap:anywhere`): chi incolla vede tutto il comando.

### Buttons
Piena notte per l'azione principale, bordo sera per la secondaria, chiara sopra i dipinti. Il disabilitato ha bordo tratteggiato e testo cenere: è uno stato atteso, non un errore.

## Do's and Don'ts

### Do:
- Mettere la prova accanto all'affermazione: i messaggi delle guardie sono quelli stampati davvero.
- Numerare solo le sequenze vere (passi di aggiornamento, passi d'installazione, righe del registro).
- Generare ogni nuova scena con la scena 1 come riferimento di stile e scrivere il prompt nel sidecar `.json` accanto al webp.
- Dipingere le stelle come punti, senza linee: Arturo sta sul prolungamento dell'arco del timone, non fa parte dell'Orsa.

### Don't:
- Non usare l'arancio fuori dalla stella.
- Non mettere un titolo display sopra le tre righe nell'apertura: la voce deve restare bassa.
- Non annidare card dentro card: le prove sono fondi di lino senza bordo.
- Non ritagliare un dipinto a caso: ogni riquadro mostra un soggetto intero o solo cielo.

## Superficie: arturo web (la pagina dei progetti)

La pagina locale di `arturo web` (ramo `dev`, `bin/web/`) estende questo mondo. I token sono una copia dei colori qui sopra, nello stesso `:root` di `bin/web/stile.css`: se cambia un colore qui, va cambiato anche lì.

### Scala e tema
- Scala tipografica fissa in rem, rapporto 1,2 (`--t-meta` .8125rem, `--t-piccolo` .875rem, `--t-testo` 1rem, `--t-lead` 1.2rem, `--t-h2` 1.44rem, `--t-h1` 2.074rem): una pagina di lavoro non cambia misura con la finestra.
- Tema scuro con `prefers-color-scheme: dark`. Tela `#1f1f29` (notte), carta `#282834` (crepuscolo), lino `#2c2d3a`, testo `#eef0ec` e `#dcdfd9`, cenere `#a9ada8`, foschia `#3b3c4a`, sera chiaro `#8cc4e6` come accento, passa `#7dcca0`, blocca `#f0968a`. L'azione piena si rovescia: fondo `#eef0ec`, testo notte.

### Segni di chi agisce
Quattro forme disegnate in CSS, mai glifi: pieno grafite = «Tocca a te», metà grafite = «Decidi tu, poi faccio io», cerchio vuoto sera = «Faccio io», lineetta cenere = «Fermo». Un chiuso è una lineetta verde. I nomi vengono sempre dai gruppi dello store, e la sintesi in testata li mette davanti a ogni frase: la sintesi fa da legenda.

### Fogli
- `.foglio`: un progetto dove qualcosa chiede una persona. Carta, filetto foschia, raggio 12 px, ombra card.
- `.foglio--dietro`: un progetto tutto in mano a Claude. Lino, nessuna ombra.
- I fogli stanno in colonne di altezza libera (`columns`), mai in una griglia di riquadri uguali. «Da dove partirei» è largo quanto la colonna, sopra il campo per aggiungere.
- Il nome del foglio passa nel titolo della pagina del progetto con una transizione di vista. Con reduced-motion, cambio secco.
