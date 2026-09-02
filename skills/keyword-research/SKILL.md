---
name: keyword-research
description: >-
  Valuta le keyword di un contenuto su tre superfici indipendenti — ricerca organica, risposte AI
  (AEO) e motori generativi (GEO) — e restituisce per ciascuna il segnale di opportunità e la scelta
  consigliata.
when_to_use: >-
  Usa quando il lavoro riguarda content strategy, SEO, piano editoriale, scelta delle keyword o
  analisi dei contenuti dei concorrenti, o quando l'utente dice «per quali parole vogliamo
  posizionarci», «conviene scrivere questa pagina?». NON per scrivere il contenuto in sé e non per
  audit tecnici del sito (crawl, sitemap, performance). Segui tutti i passi nell'ordine: non prendere
  scorciatoie basandoti su questa description.
---

# Keyword Research — Framework Tri-Superficie

## Passo 1 — Valuta ogni keyword con le 3 lenti

Le superfici sono tre e si giudicano separatamente; i riferimenti che seguono calibrano il giudizio, non sono cutoff che decidono da soli.

| Superficie | Cos'è | Segnale di opportunità |
|------------|-------|------------------------|
| **ORG** (Organico) | Risultati classici Google (link blu) | Volume alto, pagine deboli in top 10 |
| **AEO** (Answer Engine) | Featured snippet, People Also Ask, Knowledge Panel | Query "how to", "what is", domande dirette |
| **GEO** (Generative Engine) | AI Overview di Google, citazioni in ChatGPT/Perplexity | Query complesse, comparative, multi-step |

### Lente 1: Intent
I modifier nella query orientano dove sta l'opportunità (esempi, non regole rigide):
- Navigazionale ("login", "sito", brand) → quasi tutto ORG; GEO tipicamente nullo (vedi Importante)
- Informazionale ("come", "cosa", "perché") → AEO forte, GEO spesso rilevante
- Commerciale ("migliore", "vs", "recensione") → GEO forte, AEO medio
- Transazionale ("comprare", "prezzo", "sconto") → ORG in primo piano, AEO/GEO marginali

### Lente 2: SERP reale (in incognito)
Guarda cosa premia davvero la SERP e lascia che sposti il giudizio:
- Featured snippet presente → segnala opportunità AEO concreta
- AI Overview presente → segnala opportunità GEO
- PAA box → rinforza l'AEO
- Top 10 con pagine deboli (DA basso, contenuto thin) → apertura ORG

### Lente 3: Volume e difficoltà
- Pesa volume, rilevanza per il business e difficoltà insieme — nessuno dei tre da solo decide.
- Traffic potential > raw volume: 300 ricerche/mese possono generare 8.000 visite se la pagina ranka per 40 varianti. Ahrefs/Semrush mostrano il "traffic potential": usa quello.

## Passo 2 — Scegli la superficie target e motiva

Per ogni keyword esprimi un giudizio per superficie (es. forte / medio / debole, o una stima 0-10 come sintesi del ragionamento), indica la **superficie target** e **motiva** in una riga. Il target è la superficie dove l'opportunità è più concreta considerate tutte le lenti.

```
| keyword | intent | ORG | AEO | GEO | superficie_target | perché |
|---------|--------|-----|-----|-----|-------------------|--------|
| come scegliere orologio | info | medio | forte | medio | AEO | snippet aggredibile, intent esplicativo |
| rolex vs omega | comm | debole | debole | forte | GEO | query comparativa, AI Overview presente |
| orologi lusso milano | trans | forte | debole | debole | ORG | intent locale/transazionale, no snippet |
```

## Passo 3 — Clusterizza per SERP overlap

Due keyword vanno nello stesso cluster solo se i top-10 risultati si sovrappongono significativamente (>40%). Un cluster = una pagina.

## Passo 4 — Passa il brief al `drafter`

Quando lavori con il `drafter` per creare contenuti:
- Specifica nel brief la **superficie target** (ORG/AEO/GEO)
- Per AEO: struttura con H2 domanda + risposta diretta nei primi 2 paragrafi
- Per GEO: struttura comparativa, citazioni, fonti verificabili
- Per ORG: focus su completezza topica, internal linking, E-E-A-T

## Importante

- **Mai il volume grezzo come criterio unico**: un output ordinato per volume non è una keyword research. Conta il traffic potential pesato con rilevanza e difficoltà.
- **Il target non è la somma più alta**: le 3 superfici sono lenti di giudizio, non un sommatore. Niente formula a punti fissi.
- **SERP reale prima di assegnare un punteggio**: i modifier dell'intent sono indizi; la SERP in incognito conferma o smentisce. Senza averla guardata, il giudizio per superficie è una supposizione.
- **GEO = 0 per query navigazionali**: l'AI Overview non appare su brand query. Verificare in incognito prima di assegnare GEO > 0.
- **Cluster per SERP overlap, mai per semantica**: keyword semanticamente simili ma con top-10 diversi sono cluster separati e pagine separate.

## Gotchas

- **Canonical + noindex = ambiguità**: la combinazione crea segnali conflittuali. Con noindex, rimuovere il canonical
- **Paginated canonicals**: `/blog?page=2` canonicalizzato a `/blog` dice a Google di ignorare tutto il contenuto profondo. Usare self-referencing canonical per ogni pagina
- **GSC impression spike ≠ ranking improvement**: di solito Google ha espanso il query set, non hai migliorato posizione
- **Cannibalizzazione nascosta**: GSC position average 8 può significare due pagine che alternano posizione 3 e 15 sulla stessa query

## Quick Wins da GSC (settimanali)

1. Posizione 11-20 con impressioni alte → ottimizza per entrare in prima pagina
2. CTR < 2% con impressioni > 500 → riscrivi title/description
3. Click = 0 con impressioni > 100 → contenuto non risponde all'intent

## Competitor Gap Analysis

Identifica gap dove il competitor:
- Ranka organicamente ma non tiene lo snippet → puoi vincere AEO prima di raggiungere la posizione organica
- Non ha contenuto ottimizzato per AI Overview → opportunità GEO first-mover
