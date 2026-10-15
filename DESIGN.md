---
name: Arturo
description: Landing di prodotto per Claude Code in italiano, con la finestra del prodotto sotto il reticolo della volta celeste.
colors:
  cielo: "#d7ebff"
  carta: "#f5f5f3"
  carta-2: "#ebebe8"
  inchiostro: "#0b0d10"
  grafite: "#2a2e35"
  cenere: "#59606a"
  filetto: "#d6d8d4"
  azione: "#0b5fff"
  azione-giu: "#0047d6"
  azione-velo: "#e3efff"
  vuoto: "#05080c"
  vuoto-2: "#10151c"
  vuoto-testo: "#e8ecf1"
  vuoto-cenere: "#9ba5b1"
  vuoto-filetto: "#232b35"
  stella: "#f2a24a"
  blocca: "#b8301d"
  passa: "#1f7a45"
  azzurro: "#cfe6ff"
  verde: "#bfe8b5"
  giallo: "#f6eeb0"
  term: "#0b0d10"
  term-testo: "#e6e9ee"
  term-cenere: "#8c96a3"
  term-tu: "#8cc2ff"
  term-filetto: "#1d232c"
  term-guardia: "#2f6fe0"
  term-guardia-testo: "#d8e6ff"
typography:
  display:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(3.4rem, 1rem + 8.6vw, 8.6rem)"
    fontWeight: 250
    lineHeight: 0.9
    letterSpacing: "0"
    fontVariation: '"wdth" 118'
  display-pagina:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.6rem, 1.3rem + 4.6vw, 5.6rem)"
    fontWeight: 250
    lineHeight: 0.95
    letterSpacing: "-0.025em"
    fontVariation: '"wdth" 114'
  headline:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.1rem, 1.3rem + 2.6vw, 3.6rem)"
    fontWeight: 300
    lineHeight: 1.02
    letterSpacing: "-0.02em"
    fontVariation: '"wdth" 112'
  title:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(1.5rem, 1.2rem + .9vw, 2rem)"
    fontWeight: 350
    lineHeight: 1.15
    letterSpacing: "-0.015em"
    fontVariation: '"wdth" 108'
  title-piccolo:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Atkinson Next, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "clamp(16.5px, .98rem + .15vw, 18px)"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.005em"
  label:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 560
    lineHeight: 1
    letterSpacing: "0.04em"
    fontVariation: '"wdth" 75'
  label-piccola:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.74rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.07em"
    fontVariation: '"wdth" 75'
  mono:
    fontFamily: "Atkinson Mono, ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  vivo: "0px"
  finestra: "4px"
spacing:
  colonna: "1280px"
  gutter: "clamp(16px, 4vw, 48px)"
  ritmo: "clamp(80px, 10vw, 152px)"
  righe: "clamp(64px, 8vw, 120px)"
components:
  barra:
    backgroundColor: "{colors.stella}"
    textColor: "{colors.inchiostro}"
    rounded: "{rounded.vivo}"
    padding: "8px clamp(16px, 4vw, 48px)"
  azione:
    backgroundColor: "{colors.azione}"
    textColor: "#ffffff"
    typography: "{typography.label}"
    rounded: "{rounded.vivo}"
    padding: "0 18px"
    height: "44px"
  azione-hover:
    backgroundColor: "{colors.azione-giu}"
  azione-grande:
    backgroundColor: "{colors.azione}"
    textColor: "#ffffff"
    typography: "{typography.label}"
    rounded: "{rounded.vivo}"
    padding: "0 26px"
    height: "60px"
  azione-scura:
    backgroundColor: "{colors.inchiostro}"
    textColor: "#ffffff"
    typography: "{typography.label}"
    rounded: "{rounded.vivo}"
    padding: "0 18px"
    height: "44px"
  azione-chiara:
    backgroundColor: "#ffffff"
    textColor: "{colors.inchiostro}"
    typography: "{typography.label}"
    rounded: "{rounded.vivo}"
    padding: "0 22px"
    height: "48px"
  azione-chiara-hover:
    backgroundColor: "{colors.cielo}"
  azione-bordo:
    textColor: "{colors.inchiostro}"
    typography: "{typography.label}"
    rounded: "{rounded.vivo}"
    padding: "0 22px"
    height: "48px"
  azione-bordo-blu:
    textColor: "{colors.azione}"
    typography: "{typography.label}"
    rounded: "{rounded.vivo}"
    padding: "0 20px"
    height: "46px"
  finestra:
    backgroundColor: "{colors.term}"
    textColor: "{colors.term-testo}"
    typography: "{typography.mono}"
    rounded: "{rounded.finestra}"
    padding: "16px 18px 18px"
  finestra-chiara:
    backgroundColor: "#ffffff"
    textColor: "{colors.grafite}"
    rounded: "{rounded.finestra}"
  comando:
    backgroundColor: "{colors.term}"
    textColor: "#eef1f4"
    typography: "{typography.mono}"
    rounded: "{rounded.finestra}"
    padding: "14px 16px"
  comando-claude:
    backgroundColor: "#ffffff"
    textColor: "{colors.inchiostro}"
    typography: "{typography.mono}"
    rounded: "{rounded.finestra}"
    padding: "14px 16px"
  comando-vuoto:
    backgroundColor: "{colors.vuoto-2}"
    textColor: "#ffffff"
    typography: "{typography.mono}"
    rounded: "{rounded.vivo}"
    padding: "12px 14px"
  pannello-cielo:
    backgroundColor: "{colors.cielo}"
    rounded: "{rounded.vivo}"
    padding: "clamp(28px, 5vw, 64px) clamp(18px, 4vw, 56px)"
  pannello-giallo:
    backgroundColor: "{colors.giallo}"
    rounded: "{rounded.vivo}"
    padding: "clamp(28px, 5vw, 64px) clamp(18px, 4vw, 56px)"
  pannello-verde:
    backgroundColor: "{colors.verde}"
    rounded: "{rounded.vivo}"
    padding: "clamp(28px, 5vw, 64px) clamp(18px, 4vw, 56px)"
  pannello-azzurro:
    backgroundColor: "{colors.azzurro}"
    rounded: "{rounded.vivo}"
    padding: "clamp(28px, 5vw, 64px) clamp(18px, 4vw, 56px)"
  campo:
    backgroundColor: "#ffffff"
    textColor: "{colors.inchiostro}"
    typography: "{typography.body}"
    rounded: "{rounded.vivo}"
    padding: "10px 12px"
    height: "46px"
---

# Design System: Arturo

## Overview

**Creative North Star: "La finestra sotto la volta"**

Arturo è un prodotto, e la pagina lo mostra al lavoro. L'oggetto principale è la finestra di Claude Code: un terminale scuro con l'ombra, dove una sessione si scrive e la guardia chiede prima dell'azione che non si annulla. Sopra e intorno c'è la volta: un cielo chiaro attraversato da un reticolo blu che disegna Boote, il manico dell'Orsa e la stella Arturo. La stella è l'unico punto arancio del cielo.

Il registro è quello delle landing di prodotto delle IA, a righe alternate. Il testo sta a sinistra o a destra, la finestra sta su una lastra piatta di colore pieno. Le lastre si alternano: cielo col reticolo, giallo, verde, azzurro. Una fascia «vuoto» quasi nera, con una grana leggera, porta i dati d'uso e la chiusura. Il resto è carta grigio caldo con filetti sottili.

La tipografia ha due voci della stessa famiglia. Archivo largo e leggero parla nei titoli. Archivo stretto in maiuscolo dà i comandi dell'interfaccia: menu, pulsanti, etichette. Atkinson Next porta il testo e Atkinson Mono porta i terminali. Gli angoli sono vivi. La pagina rifiuta la pagina-documento numerata e l'hero scuro col terminale al neon.

**Key Characteristics:**
- Il cielo `cielo` col reticolo generato della volta, in apertura e in una lastra per pagina.
- La finestra del prodotto come unico oggetto con ombra.
- Righe alternate su lastre piatte di quattro colori, senza bordo e senza raggio.
- Archivo largo e leggero per i titoli, Archivo stretto maiuscolo per l'interfaccia.
- Angoli da 0 a 4 px. Il pulsante principale è un blocco blu pieno e squadrato.
- L'arancio solo sulla stella e sulla barra in cima.

## Colors

Una palette fredda e chiara: cielo azzurro, carta grigio caldo, inchiostro quasi nero, un solo blu d'azione e un arancio che compare due volte.

### Primary
- **Blu Azione** (`azione`): il pulsante principale («Installa Arturo»), la selezione del testo, il contorno del focus, le icone delle etichette, le linee di Boote e dell'Orsa nel reticolo. Al passaggio del mouse scende a **Blu Azione Fondo** (`azione-giu`). **Velo Azione** (`azione-velo`) è il fondo leggero del passo corrente nella guida e dello strato scelto nella pagina per le organizzazioni.

### Secondary
- **Stella** (`stella`): l'arancio di Arturo. Vive nella stella del reticolo e nel suo alone, nel punto del marchio, nella favicon e nella barra sottile in cima alla home.

### Tertiary
- **Lastre** (`giallo`, `verde`, `azzurro`, più `cielo` col reticolo): i fondi pieni delle righe alternate. Ognuna ospita una sola finestra.

### Neutral
- **Cielo** (`cielo`): fondo dell'apertura, delle testate, della pagina d'accesso e della lastra col reticolo. È anche il `theme-color`.
- **Carta** (`carta`) e **Carta Scura** (`carta-2`): il fondo della pagina e il fondo dei `code` in linea, dei messaggi dell'utente nella chat d'esempio e dei segni «dove si incolla».
- **Inchiostro** (`inchiostro`): titoli, il filetto che apre ogni elenco, il pulsante scuro del menu.
- **Grafite** (`grafite`): il testo corrente. **Cenere** (`cenere`): seconde righe dei titoli, didascalie, etichette quiete. **Filetto** (`filetto`): le linee tra le voci.
- **Vuoto** (`vuoto`, `vuoto-2`, `vuoto-testo`, `vuoto-cenere`, `vuoto-filetto`): la fascia scura con la grana, i suoi comandi e i suoi filetti.
- **Terminale** (`term`, `term-testo`, `term-cenere`, `term-tu`, `term-filetto`): la finestra di Claude Code. `term-tu` colora quello che scrive la persona. `term-filetto` separa barra e righe dentro la finestra.
- **Esiti** (`passa`, `blocca`): il verde dei passi fatti e il rosso degli errori nella guida e nell'accesso. Nei terminali «Chiede a te» è `term-tu` su bordo `term-guardia`, col testo del messaggio in `term-guardia-testo`. «Blocca» usa ancora tinte letterali (`#ff9a8a` su bordo `#a8382a`).

### Dove stanno
Tutti i token di colore, carattere e misura stanno in `sito/stile/colori.css`, caricato da ogni pagina prima del suo `<style>`. Una pagina tiene nel suo `:root` solo i token che usa lei sola (`--esce`, `--segno` nella guida). `/stile/` è pubblico come `/font/`, perché serve anche a `/entra`.

### Named Rules
**The Una Stella Rule.** L'arancio `stella` compare solo nella stella Arturo (reticolo, alone, marchio, favicon) e nella barra in cima. Mai su pulsanti, titoli, etichette o lastre.

**The Un Solo Blu Rule.** Tutto ciò che si clicca per andare avanti è `azione`. Il reticolo usa lo stesso blu, così il cielo e il pulsante parlano la stessa lingua.

## Typography

**Display Font:** Archivo variabile (larghezza 62-125%, peso 100-900), con Helvetica Neue e Arial
**Body Font:** Atkinson Next (Atkinson Hyperlegible Next), con system-ui
**Label/Mono Font:** Archivo stretto per le etichette, Atkinson Mono (Atkinson Hyperlegible Mono) per i terminali

**Character:** Archivo largo e leggero dà ai titoli un respiro ampio e tecnico. Lo stesso Archivo stretto in maiuscolo dà all'interfaccia il tono di un pannello di controllo. Atkinson tiene il testo leggibile per chi non è tecnico. Tutti i font sono OFL e ospitati in `sito/font/`.

### Hierarchy
- **Display** (250, larghezza 118%): la parola «ARTURO» in apertura, una lettera per colonna, distribuita su tutta la larghezza.
- **Display Pagina** (250, larghezza 114%): il titolo d'apertura della guida e della pagina per le organizzazioni.
- **Headline** (300, larghezza 112%): i titoli di sezione. Spesso hanno una seconda riga in `cenere`, sullo stesso corpo.
- **Title** (350, larghezza 108%): i titoli delle righe alternate, con la seconda riga in `cenere`.
- **Title Piccolo** (400, larghezza normale): i titoli delle colonne con filetto (`tre`, impegni, voci della pagina per le organizzazioni).
- **Body** (400, 16,5-18 px fluido): testo corrente, misura tra 46 e 70 caratteri.
- **Label** (560, larghezza 75%, maiuscolo): menu, pulsanti, etichette sotto la promessa.
- **Label Piccola** (600, larghezza 75%, maiuscolo): esiti, intestazioni di tabella, titoli del piede, stato dei passi.
- **Mono** (400): sessioni, comandi, registro delle guardie, barra delle finestre.

### Named Rules
**The Due Larghezze Rule.** Archivo è largo (112-118%) e leggero (250-300) nei titoli grandi. È stretto (75%) e maiuscolo nell'interfaccia. Le larghezze intermedie servono solo al marchio e ai titoli di riga (108%).

**The Terminale Mono Rule.** Atkinson Mono compare dentro le finestre, nei comandi da copiare e nei `code`. Fuori dal terminale il testo è sempre Atkinson Next.

## Layout

Una colonna di `colonna` con `gutter` fluido. Le sezioni distano `ritmo`. Le testate di sezione sono a due colonne uguali: titolo a sinistra, attacco a destra, allineati in basso.

Le funzioni stanno in righe alternate distanti `righe`. Il testo prende 5/12, la lastra 7/12, e le righe pari invertono il lato. La fascia dei dati d'uso usa lo stesso 5/12 e 7/12. La guida d'installazione ha un indice fisso a sinistra (300 px) e il passo aperto a destra.

Ogni griglia usa `minmax(0, 1fr)`, così un comando lungo va a capo e la pagina non sborda. La home passa a una colonna sotto 1020 px per le righe e sotto 760 px per il resto. Su mobile l'apertura mette prima la promessa e poi la finestra. La guida passa a una colonna sotto 980 px.

## Elevation & Depth

La pagina è piatta. La profondità sta in un solo oggetto: la finestra del prodotto, che si stacca dal cielo o dalla lastra con un'ombra lunga e morbida. Tutto il resto si separa con filetti, lastre di colore e la fascia scura.

### Shadow Vocabulary
- **Finestra** (`box-shadow: 0 1px 2px rgba(5,8,12,.18), 0 18px 40px -12px rgba(5,8,12,.38)`): la finestra di Claude Code nella home e nella pagina per le organizzazioni.
- **Schermo atteso** (`box-shadow: 0 0 0 1px rgba(11,13,16,.12), 0 14px 32px -16px rgba(5,8,12,.35)`): la finestra chiara che nella guida mostra cosa vedrai.
- **Anello** (`box-shadow: inset 0 0 0 1px var(--inchiostro)`): un bordo disegnato con l'ombra interna, sui segni «Claude», sul comando da incollare in Claude e sul riquadro dei dati. Non dà profondità.

### Named Rules
**The Solo Finestre Rule.** Le finestre del prodotto sono l'unico oggetto con ombra. Pulsanti, lastre, card, tabelle e campi restano piatti.

## Shapes

Gli angoli sono vivi. Le finestre e le bolle della chat d'esempio hanno 4 px (`finestra`). Pulsanti, lastre, campi, comandi sulla fascia scura e segni sono a 0 px (`vivo`). Il cerchio compare solo nei tre puntini della barra delle finestre, nelle stelle del reticolo e nel punto del richiamo della guida. I campi hanno solo il filetto in basso, come un modulo cartaceo. Gli strati della pagina per le organizzazioni sono quattro cornici a filo, una dentro l'altra.

### Named Rules
**The Zero-Quattro Rule.** I raggi vanno da 0 a 4 px. Il 4 è per le finestre, lo 0 per tutto il resto.

## Components

### Buttons
Blocchi squadrati, con la voce stretta e maiuscola.
- **Shape:** angoli vivi (`vivo`), bordo di 1 px dello stesso colore del fondo.
- **Primary:** fondo `azione`, testo bianco. Alto 44 px nel menu, 60 px nella versione grande dell'apertura.
- **Hover / Focus:** il fondo scende ad `azione-giu` in 0,18 s. Il focus è un contorno di 2 px `azione` staccato di 3 px.
- **Scura:** fondo `inchiostro`, per «Installa» nel menu.
- **Chiara:** fondo bianco e testo `inchiostro` sulla fascia scura, al passaggio diventa `cielo`.
- **Bordo:** fondo trasparente, bordo e testo `inchiostro` nella pagina per le organizzazioni. Nella guida il bordo è blu `azione` e il passaggio stende `azione-velo`.

### Etichette e segni
- **Etichette della promessa:** voce stretta maiuscola con un'icona SVG di 15 px in `azione`, senza fondo.
- **Esiti nel terminale:** riquadro con bordo di 1 px, voce stretta maiuscola, nessun raggio.
- **Dove si incolla (guida):** tre segni alti 24 px. Terminale: fondo `inchiostro`. Claude: fondo bianco con anello `inchiostro`. Pagina: fondo `carta-2`.

### Lastre (righe alternate)
- **Corner Style:** angoli vivi.
- **Background:** `cielo` con `img/volta.svg`, `giallo`, `verde`, `azzurro`. Dal 15/10 la home non le usa più: «Cosa fa Arturo» è una riga di quattro voci con un filetto `inchiostro` sopra ciascuna. Restano per le altre pagine.
- **Shadow Strategy:** nessuna. L'ombra sta solo sulla finestra che la lastra contiene.
- **Border:** nessuno.
- **Internal Padding:** `clamp(28px, 5vw, 64px)` in verticale, `clamp(18px, 4vw, 56px)` in orizzontale. Larghezza della finestra al massimo 560 px.

### Inputs / Fields
- **Style:** fondo bianco, solo filetto `inchiostro` in basso, angoli vivi, alto 46 px.
- **Focus:** il filetto diventa `azione` e si ispessisce con un'ombra interna di 2 px. Il cursore è `azione`.
- **Accesso:** nella pagina d'accesso campo e pulsante stanno uniti in una riga, con bordo pieno `inchiostro`. L'errore usa `blocca`.

### Navigation
Il marchio (colline, stella arancio, «Arturo» in Archivo 500 a larghezza 108%) sta a sinistra. Le voci stanno in fila, in voce stretta maiuscola, con un filetto che compare sotto al passaggio. «Installa» chiude a destra come pulsante scuro. Sotto 1020 px restano marchio e pulsante. Sopra il menu, nella home, corre la barra arancio sottile.

### Finestra del prodotto (componente firma)
Il terminale di Claude Code: fondo `term`, raggio 4 px, ombra Finestra. Una barra di 34 px con tre puntini e il titolo in mono centrato. Dentro, la sessione: le righe della persona in `term-tu` dopo «> », le azioni con un punto verde, la guardia in un riquadro con bordo blu e il titolo in grassetto chiaro, la scelta evidenziata in blu pieno. La variante chiara (fondo bianco, barra `#fbfbfa`) mostra la chat d'esempio.

I messaggi delle guardie sono quelli che Arturo stampa davvero, con i loro apostrofi dritti. Le sessioni intorno sono esempi, e la didascalia lo dichiara («Sessione di esempio», «Esempio scritto per questa pagina»). Nell'apertura la finestra ha due schede, «Cosa ci fai» e «Installalo», sottolineate in `term-tu` quando sono scelte. «Cosa ci fai» è una galleria di sessioni: una per volta, cambia ogni 7 s con una dissolvenza da sfocato, si ferma al passaggio del mouse, al fuoco e al primo clic; sotto, frecce e nomi delle sessioni. «Installalo» sono carte in sequenza con i primi quattro passi della guida, Mac o Windows, il comando da copiare e «Fatto, avanti»; scrivono lo stesso stato della guida (`arturo-setup-1`), che riparte dal passo 5. Con movimento ridotto niente scorre e niente sfuma.

### La volta (componente firma)
Il reticolo è generato da uno script, in proiezione gnomonica centrata su Boote, e non è disegnato a mano. Meridiani e paralleli sono linee blu `#2b8cff` a opacità 0,5, larghe 1 px a ogni scala. Boote e l'Orsa sono spezzate `azione` da 1,6 px con stelle a punti. Un arco tratteggiato in `inchiostro` porta dal timone dell'Orsa ad Arturo. Arturo è un punto `stella` con un alone che si allarga in 4,8 s. Con movimento ridotto l'alone resta fermo. Una maschera a gradiente lo schiarisce a sinistra, dove sta il testo.

### Fascia vuoto
Fondo `vuoto` con una grana a rumore frattale al 13%. Porta i dati d'uso (tabella degli eventi, parole barrate di ciò che non esce mai, comandi da copiare) e la chiusura con il pulsante chiaro. I comandi qui sono piatti, con un bordo e senza raggio.

### Schema dell'harness
Tre cerchi concentrici: fuori `cielo` con bordo `azione` (Arturo), in mezzo bianco con bordo `inchiostro` (Claude Code), dentro `inchiostro` pieno (il modello). I nomi corrono lungo gli archi in voce stretta maiuscola. Un punto `stella` sull'anello esterno è Arturo. È l'unico posto dove il cerchio fa da forma.

### Articoli e iscrizione
Un elenco di quattro righe sotto un filetto `inchiostro`: data in voce stretta, titolo in Archivo 1,15 rem. Accanto, l'iscrizione. L'elenco nella pagina è di riserva e lo rinfresca `strumenti/articoli.py`; nel browser lo sostituisce la Content API di Ghost. L'iscrizione è il modulo di Ghost (`sito/vendor/`), con il pulsante `azione`.

### Casi d'uso e «In breve»
I casi d'uso sono sei finestre piccole su tre colonne, una richiesta e una risposta ciascuna, con una didascalia di una riga. La parte tecnica è una riga di quattro voci come «Cosa fa Arturo» (cosa serve, comandi, memoria, telemetria), una frase ciascuna: il dettaglio sta su GitHub.

### Guida a tappe
Ogni tappa ha una boa quadrata di 40 px. La tappa corrente ha la boa piena `azione` e un velo `azione-velo` che sfuma verso destra. La tappa fatta ha la boa con bordo `passa` e una spunta. Il passo si apre con una piega di 0,5 s sulla curva `--esce`.

## Do's and Don'ts

### Do:
- **Do** mettere ogni finestra su una lastra piatta o sul cielo, mai sulla carta nuda nelle righe alternate.
- **Do** alternare il lato del testo a ogni riga e cambiare lastra a ogni riga (cielo col reticolo, giallo, verde, azzurro).
- **Do** stampare nei terminali i messaggi veri delle guardie, e dichiarare nella didascalia che la sessione è un esempio.
- **Do** usare Archivo largo e leggero (112-118%, 250-300) per i titoli e Archivo stretto maiuscolo (75%) per menu, pulsanti ed etichette.
- **Do** dare ai titoli di sezione la seconda riga in `cenere` sullo stesso corpo.
- **Do** rigenerare il reticolo con lo script quando serve un'inquadratura nuova della volta.

### Don't:
- **Don't** usare l'arancio `stella` fuori dalla stella Arturo e dalla barra in cima.
- **Don't** dare ombra a qualcosa che non sia una finestra del prodotto.
- **Don't** superare i 4 px di raggio, né usare il cerchio fuori dai puntini delle finestre, dalle stelle del reticolo, dal punto del richiamo e dallo schema dell'harness.
- **Don't** usare Atkinson Mono fuori dai terminali, dai comandi e dai `code`.
- **Don't** inventare il messaggio di una guardia: se il testo non è quello che Arturo stampa, non va in un terminale.
- **Don't** mettere bordi o raggi sulle lastre delle righe alternate.

## Superficie: arturo web (la pagina dei progetti)

La pagina locale di `arturo web` (ramo `dev`, `bin/web/`) usa ancora la palette del mondo precedente, «la stella dei naviganti», nel `:root` di `bin/web/stile.css`: tela `#fefffc`, carta `#ffffff`, lino `#f9faf7`, inchiostro `#171717`, grafite `#2c2c2c`, carbone `#444141`, cenere `#646464`, nebbia `#b4b8b4`, foschia `#dee2de`, crepuscolo `#282834`, notte `#1f1f29`, sera `#2b6f9e`, sera chiaro `#8cc4e6`, mare `#0d5e8f`, passa `#2f7a4f`, blocca `#b2392b`, arturo `#f2a24a`. Questi colori non sono i token qui sopra. La pagina va riallineata al mondo nuovo in un lavoro a parte.

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
