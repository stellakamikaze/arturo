// Le misure comuni del mod (fase 4 del piano di design, #5371): una scala sola per spazi, raggi, testo,
// pulsanti e icone, così la colonna di sinistra, la testata e i pannelli non inventano ognuno la sua.
// Base 4. Un numero fuori da qui, in una parte, è un'eccezione da spiegare accanto.

// Spazi: padding, margini e distanze fra elementi.
export const SPAZIO = { xs: 2, s: 4, m: 8, l: 12, xl: 16, xxl: 24 };

// Il bordo della colonna di sinistra: pulsanti, campo, interruttore, gruppi e righe partono tutti da qui.
export const MARGINE = SPAZIO.l;

// Raggi: controlli (pulsanti piccoli, pastiglie), righe e carte, riquadri.
export const RAGGIO = { controllo: 6, riga: 8, riquadro: 10 };

// Corpi del testo.
export const TESTO = { nota: 11.5, etichetta: 12.5, corpo: 13.5, riga: 14, testata: 16, titolo: 20 };

// Pulsanti in due altezze: grande per le azioni della colonna, piccolo per quelli dentro una riga.
export const PULSANTE = { grande: 36, piccolo: 28 };

// Icone e pallino di stato.
export const ICONA_MISURA = { piccola: 14, grande: 16 };
export const PALLINO = 7;

// Il piede della colonna: una fila di icone. Il layout gli dà questa altezza (layouts/arturo.json).
export const PIEDE = 44;
