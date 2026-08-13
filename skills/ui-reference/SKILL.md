---
name: ui-reference
description: Si attiva quando il task coinvolge sviluppo frontend, componenti UI, CSS, Tailwind, layout, responsive design, dark mode, accessibilita', animazioni, design system, o quando l'utente chiede di costruire/modificare interfacce. Fornisce checklist concrete, valori precisi e gotchas per evitare errori comuni di UI.
---

# UI Reference — Checklist e Gotchas

## Design Direction

Prima di scrivere codice, scegli una direzione estetica precisa e impegnati: minimalist, maximalist, retro-futuristic, luxury, editorial, brutalist, ecc. Differenziazione intenzionale tra progetti diversi.

**Il test critico**: "Se mostrassi questo a qualcuno dicendo 'lo ha fatto l'AI', ci crederebbe subito? Se si', e' un problema."

## AI Slop Detection — Segnali di Design Templato

Il principio è uno: **design intenzionale, non uscito da un template di default.** La tabella sotto raccoglie i segnali oggi più comuni di "look da AI" — sono **esempi orientativi, non una blocklist esaustiva né vincolante**: la moda cambia, e ognuna di queste scelte può essere giusta se è deliberata e serve la direzione estetica. Usali per accorgerti quando stai scivolando nel default, non come divieti.

| Categoria | Segnale comune |
|-----------|-------------|
| Font | Inter, Roboto, Open Sans, Arial come scelta default senza motivo |
| Colori | Gradienti cyan/purple, neon/glow accents, grigi puri senza tinta brand |
| Layout | Card grid identiche ripetute, centrare tutto, rounded rectangles ovunque |
| Effetti | Glassmorphism generico, drop shadow senza scopo |
| Dark mode | Nero puro `#000` + neon come default |
| Copy | "Something went wrong", loading in stile "AI making magic" |

## Layout: 4-Point Grid System

Tutti gli spacing usano la scala 4-point: `4, 8, 12, 16, 24, 32, 48, 64, 96px`
- Padding componenti: 16px (compact) / 24px (standard) / 32px (spacious)
- Gap tra elementi: 8px (tight) / 16px (normal) / 24px (loose)
- Token semantici: `--space-sm`, `--space-lg` (non `--space-16`)

Grid responsive senza media query:
```css
grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
```
`auto-fit` non `auto-fill` — evita colonne vuote fantasma.

**Squint test**: sfuoca la vista — gli elementi importanti devono restare identificabili.

**Card**: appropriate solo quando il contenuto e' distinto e azionabile. Mai annidare card dentro card.

**Container queries**: `container-type: inline-size` per componenti che si adattano alla propria larghezza, non al viewport.

## Typography

### Scale 1.25

| Livello | Size | Line-height |
|---------|------|-------------|
| xs | 12px / 0.75rem | 1.5 |
| sm | 14px / 0.875rem | 1.5 |
| base | 16px / 1rem | 1.5 |
| lg | 18px / 1.125rem | 1.4 |
| xl | 20px / 1.25rem | 1.3 |
| 2xl | 24px / 1.5rem | 1.3 |
| 3xl | 30px / 1.875rem | 1.2 |
| 4xl | 36px / 2.25rem | 1.1 |

### Font — spunti, non una lista chiusa

I font a sinistra sono quelli diventati il default riconoscibile del "look da AI": non sono vietati, ma sceglierli richiede un motivo, non l'inerzia. A destra, alternative valide oggi — **esempi per rompere lo schema, non prescrizioni**: il font giusto dipende dalla direzione estetica del progetto, e questa mappa invecchia.

| Default riconoscibile | Alternative (esempi) |
|-----------|-----|
| Inter | Instrument Sans, Plus Jakarta Sans, Outfit |
| Roboto | Onest, Figtree, Urbanist |
| Open Sans | Source Sans 3, Nunito Sans, DM Sans |
| Editorial/premium | Fraunces, Newsreader, Lora |

Spesso un solo font con pesi multipli crea gerarchia piu' pulita di due font in competizione.

### Regole

- Mai `px` per body text — solo `rem`/`em`. Minimo 16px body.
- `clamp()` solo per heading su pagine marketing. Per app UI/dashboard: scale fisse con rem.
- 45-75 caratteri per riga ottimale.
- `font-variant-numeric: tabular-nums` per tabelle dati.
- Vertical rhythm: line-height come unita' base per spacing verticale.

## Colori

### OKLCH invece di HSL

HSL non e' percettivamente uniforme (50% lightness in yellow ≠ 50% in blue). OKLCH si'.

```css
/* Sintassi: oklch(lightness% chroma hue) */
--primary: oklch(55% 0.25 250);      /* lightness 0-100%, chroma 0-0.4+, hue 0-360 */
```

### Regola 60-30-10

- 60% colore dominante (background, superfici)
- 30% colore secondario (card, sidebar, accent areas)
- 10% colore accent (CTA, link, badge, stati attivi)

### Tinted Neutrals

Invece di grigio puro, aggiungere chroma minima con tinta brand:
```css
--neutral-warm: oklch(95% 0.01 60);   /* warm */
--neutral-cool: oklch(95% 0.01 250);  /* cool */
```

### Dark Mode — Elevation, Non Inversione

Non invertire i colori. Usare superfici a elevazione crescente:

```css
:root[data-theme="dark"] {
  --surface-0: oklch(13% 0.01 250);   /* base */
  --surface-1: oklch(18% 0.01 250);   /* card */
  --surface-2: oklch(23% 0.01 250);   /* elevated */
  --text-primary: oklch(93% 0.01 250);
  --text-secondary: oklch(65% 0.02 250);
  --border: oklch(30% 0.01 250);
}
```

**Nero e bianco puro (`#000`, `#fff`) sono il tell #1 dell'amateur.**

### Contrasto WCAG

- Body text AA: 4.5:1, AAA: 7:1
- Large text/UI (18px+): AA 3:1, AAA: 4.5:1
- Placeholder text: ancora 4.5:1 (errore comune ignorarlo)

## Bottoni: Hierarchy a 3 Livelli

1. **Primary**: background pieno, colore accent, 1 per schermata
2. **Secondary**: outline o tinted background, azioni secondarie
3. **Ghost**: solo testo, azioni terziarie, navigazione

## Interaction: 8 Stati Obbligatori

Ogni elemento interattivo richiede tutti e 8:

| Stato | Quando | Trattamento |
|-------|--------|-------------|
| Default | A riposo | Stile base |
| Hover | Pointer sopra (non touch) | Lift sottile, shift colore |
| Focus | Keyboard/programmatico | Ring visibile 2-3px, offset 2px |
| Active | Mentre premuto | `scale(0.98)`, piu' scuro |
| Disabled | Non interattivo | Opacity ridotta, `pointer-events: none` |
| Loading | Processing | Spinner o skeleton |
| Error | Stato invalido | Red border + icon + messaggio |
| Success | Completato | Green check, conferma |

### Focus Rings

```css
button:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```
Contrasto minimo 3:1, spessore 2-3px. Mai `outline: none` senza `focus-visible`.

### Dialog e Popover Nativi

- `<dialog>` con `.showModal()`: auto focus-trap, chiude su Escape, `inert` sul contenuto dietro.
- Popover API per tooltip/dropdown: light-dismiss, stacking automatico, accessibilita' built-in.

### Undo > Confirm

Undo e' migliore dei dialog di conferma (gli utenti ignorano i prompt). Rimuovere subito dall'interfaccia, mostrare toast undo, eseguire dopo scadenza. Riservare conferme solo per azioni irreversibili (pagamenti, cancellazioni permanenti).

## Motion Design

### Durate

| Durata | Use Case | Esempi |
|--------|----------|--------|
| 100-150ms | Feedback istantaneo | Button press, toggle, color |
| 200-300ms | Cambi di stato | Menu, tooltip, hover |
| 300-500ms | Layout changes | Accordion, modal, drawer |
| 500-800ms | Entrance animations | Page load, hero reveals |

Exit = 75% della durata entrance.

### Easing — Mai `ease` Generico

```css
--ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);   /* smooth, default */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);    /* snappy, confident */
--ease-in:        cubic-bezier(0.7, 0, 0.84, 0);    /* uscita */
--ease-in-out:    cubic-bezier(0.65, 0, 0.35, 1);   /* toggle */
```

Bounce e elastic curves: amateurish. Evitare.

### Regole

- Solo `transform` e `opacity`. Per height: `grid-template-rows: 0fr → 1fr`.
- Stagger: `animation-delay: calc(var(--i) * 50ms)`. Cappare il totale.
- Soglia 80ms: sotto sembra istantaneo (brain buffer).

### Reduced Motion — Non Opzionale

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Responsive Design

### Mobile-First

Stili base per mobile, poi `min-width` media queries. 3 breakpoint bastano: 640, 768, 1024px.
Breakpoint content-driven: espandi finche' non si rompe, inserisci li' il breakpoint.

### Rilevare Input, Non Screen Size

```css
@media (pointer: fine)   { .button { padding: 8px 16px; } }
@media (pointer: coarse) { .button { padding: 12px 20px; } }
@media (hover: hover)    { .card:hover { transform: translateY(-2px); } }
@media (hover: none)     { /* no hover-dependent interactions */ }
```

### Safe Areas (Notch)

```css
body { padding-top: env(safe-area-inset-top); }
.footer { padding-bottom: max(1rem, env(safe-area-inset-bottom)); }
```
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

### Responsive Images

```html
<img srcset="hero-400.jpg 400w, hero-800.jpg 800w, hero-1200.jpg 1200w"
     sizes="(max-width: 768px) 100vw, 50vw" src="hero-800.jpg" alt="...">
```
`<picture>` per art direction (composizioni diverse per breakpoint diversi).

## UX Writing

- **Verb + Object**: "Save changes", "Delete message" — mai "Submit", "OK", "Yes/No"
- **Formula errori**: cosa e' successo + perche' + come risolvere. Non incolpare l'utente.
- **Azioni distruttive**: specificare cosa viene rimosso e conteggi. "Delete 3 messages" non "Delete".
- **Empty states**: trattarli come onboarding con value proposition chiara.
- **i18n**: pianificare espansione testo (tedesco +30%, francese +20%).

## Touch Target

Minimo **44x44px** per mobile (WCAG 2.5.5). Se il visual e' piu' piccolo, estendi l'area cliccabile con padding o pseudo-elementi.

## Feedback: Toast System

| Tipo | Comportamento |
|------|--------------|
| Success | Auto-dismiss 3-5s |
| Error | Persiste, chiusura manuale |
| Warning | Auto-dismiss 8s |
| Info | Auto-dismiss 5s |

Max 3 toast visibili. Stack dal basso. `role="alert"` per screen reader.

## Data Tables

- Numeri: allineati a **destra**, `font-variant-numeric: tabular-nums`
- Testo: allineato a **sinistra**
- Non mescolare righe zebrate + hover highlight — scegliere uno

## Gotchas

> **Stack primario = Vue 3 + SCSS (no Tailwind)**. Preferire variabili/mixin SCSS, `:deep()`, scoped styles. I due gotcha Tailwind sotto valgono SOLO se il progetto monta effettivamente Tailwind.

- **Mobile Safari 100vh**: usare `min-height: 100dvh` con fallback `-webkit-fill-available`
- **Focus ring + transform**: `scale()` clippa `box-shadow`. Usare `outline` con `outline-offset`
- **CSS custom properties e teleport**: variabili `:root` non raggiungono nodi montati fuori dal DOM tree (Vue `<Teleport>`, portali React)
- **Tailwind + CSS vars** (solo progetti Tailwind): `bg-[--color-name]` (con `--`). Senza `--`, fallisce silenziosamente
- **Tailwind purge** (solo progetti Tailwind): classi dinamiche (`bg-${color}-500`) rimosse. Usare classi complete o safelist
- **Optical alignment**: centramento matematico ≠ visivo. Testo nei bottoni: +1-2px padding-top
- **CLS**: sempre `width`/`height` o `aspect-ratio` su immagini
- **Lazy loading above the fold**: mai su hero/LCP. Usare `fetchpriority="high"` + `loading="eager"`
- **z-index**: scala ordinata (`--z-dropdown: 100`, `--z-modal: 200`, `--z-toast: 300`)

## Accessibilita' Minima

- Contrasto: vedi sezione Colori sopra
- `aria-label` su icon button senza testo visibile
- `aria-describedby` per messaggi errore nei form
- Skip link come primo elemento focusable
- `prefers-reduced-motion`: vedi sezione Motion sopra
- Placeholder non sono label — sempre `<label>` visibili
- Roving tabindex per gruppi (tabs, menu): un solo elemento tabbable, arrow keys navigano

## Performance UI

- **Preload hero**: `<link rel="preload" as="image" fetchpriority="high">`
- **Code splitting**: `React.lazy()` per route e modali pesanti
- **Bundle**: `import debounce from 'lodash/debounce'` mai `import _ from 'lodash'`
- **Core Web Vitals target**: LCP <2.5s, INP <200ms, CLS <0.1
