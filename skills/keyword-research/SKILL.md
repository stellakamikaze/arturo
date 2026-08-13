---
name: keyword-research
description: Si attiva quando il task coinvolge content strategy, SEO, pianificazione editoriale, scelta keyword, analisi competitor contenuti, o quando l'utente menziona keyword, SERP, ranking, traffico organico, featured snippet, AI Overview. Fornisce il framework tri-superficie per scorare keyword su 3 assi (organico, AEO, GEO) e guidare la strategia contenuti.
---

# Keyword Research — Framework Tri-Superficie

Ogni keyword si valuta su 3 superfici indipendenti. Le 3 superfici sono **lenti di giudizio**, non un sommatore: pesa i segnali di ciascuna e scegli la superficie target motivando la scelta, invece di sommare punti fissi. Il contenuto si ottimizza per la superficie dove l'opportunità è più concreta — che è un giudizio editoriale sul singolo caso, non l'uscita di una formula.

## Le 3 Superfici

| Superficie | Cos'e' | Segnale di opportunita' |
|------------|--------|------------------------|
| **ORG** (Organico) | Risultati classici Google (link blu) | Volume alto, pagine deboli in top 10 |
| **AEO** (Answer Engine) | Featured snippet, People Also Ask, Knowledge Panel | Query "how to", "what is", domande dirette |
| **GEO** (Generative Engine) | AI Overview di Google, citazioni in ChatGPT/Perplexity | Query complesse, comparative, multi-step |

## Come valutare (le 3 lenti)

Per ogni keyword, guarda i segnali sotto e formati un giudizio su quanto è aggredibile ciascuna superficie. I riferimenti che seguono servono a calibrare il giudizio, non sono cutoff che decidono da soli: il target emerge dal ragionamento, non da una somma.

### Lente 1: Intent
I modifier nella query orientano dove sta l'opportunità (esempi, non regole rigide):
- Navigazionale ("login", "sito", brand) → quasi tutto ORG; su brand query l'AI Overview di solito non appare, quindi GEO è tipicamente nullo
- Informazionale ("come", "cosa", "perche'") → AEO forte, GEO spesso rilevante
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
- Traffic potential > raw volume: 300 ricerche/mese possono generare 8.000 visite se la pagina ranka per 40 varianti. Non usare mai il volume grezzo come criterio unico.

### Output
Per ogni keyword esprimi un giudizio per superficie (es. forte / medio / debole, o una stima 0-10 come sintesi del ragionamento), indica la **superficie target** e **motiva** in una riga. Il target non è la somma più alta: è la superficie dove l'opportunità è più concreta considerate tutte le lenti.

```
| keyword | intent | ORG | AEO | GEO | superficie_target | perché |
|---------|--------|-----|-----|-----|-------------------|--------|
| come scegliere orologio | info | medio | forte | medio | AEO | snippet aggredibile, intent esplicativo |
| rolex vs omega | comm | debole | debole | forte | GEO | query comparativa, AI Overview presente |
| orologi lusso milano | trans | forte | debole | debole | ORG | intent locale/transazionale, no snippet |
```

## Clustering per SERP Overlap (non per semantica)

Due keyword vanno nello stesso cluster SOLO se i top-10 risultati si sovrappongono significativamente (>40%). Keyword semanticamente simili ma con SERP diversi = cluster separati = pagine separate.

## Gotchas

- **Traffic potential vs volume**: non usare mai raw volume come unico criterio. Ahrefs/Semrush mostrano "traffic potential" — usalo
- **GEO = 0 per query navigazionali**: AI Overview non appare su brand query. Verificare in incognito prima di assegnare GEO > 0
- **Canonical + noindex = ambiguita'**: la combinazione crea segnali conflittuali. Con noindex, rimuovere il canonical
- **Paginated canonicals**: `/blog?page=2` canonicalizzato a `/blog` dice a Google di ignorare tutto il contenuto profondo. Usare self-referencing canonical per ogni pagina
- **GSC impression spike ≠ ranking improvement**: di solito Google ha espanso il query set, non hai migliorato posizione
- **Cannibalizzazione nascosta**: GSC position average 8 puo' significare due pagine che alternano posizione 3 e 15 sulla stessa query
- **SERP overlap = criterio cluster**: due keyword semanticamente simili ma con top-10 diversi sono cluster separati

## Quick Wins da GSC (settimanali)

1. Posizione 11-20 con impressioni alte → ottimizza per entrare in prima pagina
2. CTR < 2% con impressioni > 500 → riscrivi title/description
3. Click = 0 con impressioni > 100 → contenuto non risponde all'intent

## Integrazione Content Strategy

Quando lavori con il `drafter` per creare contenuti:
- Specifica nel brief la **superficie target** (ORG/AEO/GEO)
- Per AEO: struttura con H2 domanda + risposta diretta nei primi 2 paragrafi
- Per GEO: struttura comparativa, citazioni, fonti verificabili
- Per ORG: focus su completezza topica, internal linking, E-E-A-T

## Competitor Gap Analysis

Identifica gap dove il competitor:
- Ranka organicamente ma non tiene lo snippet → puoi vincere AEO prima di raggiungere la posizione organica
- Non ha contenuto ottimizzato per AI Overview → opportunita' GEO first-mover
