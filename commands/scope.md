---
description: Crea documento tecnico dettagliato - architettura, API, database, componenti
---

# Scope Tecnico

Crea un documento di scope tecnico basato sulla discovery completata. Questo documento definisce COSA verrà costruito e COME sarà strutturato.

## Prerequisiti

Questo comando va eseguito DOPO `/discovery`. Se non è stata fatta discovery, chiedi:
- Nome progetto
- Problema da risolvere
- Lista feature MVP
- Preferenze stack tecnico

## Struttura Documento

Deriva architettura e stack dal progetto reale (dalla discovery), non da un template. Le sezioni sotto sono un menu: includi quelle pertinenti allo stack scelto e ometti quelle che non hanno senso — una CLI non ha "Flusso Frontend", una libreria non ha "Schema Database", uno script dati non ha "Endpoint API". Aggiungi sezioni proprie del dominio se servono.

### 1. Diagramma Architettura
Diagramma ASCII dei componenti reali e delle loro relazioni: flusso dei dati/controllo, integrazioni esterne (API, servizi), confini principali. La forma dipende dal sistema (web full-stack, CLI, servizio, libreria, pipeline…).

### 2. Struttura Progetto
Albero delle directory secondo lo stack e le convenzioni scelti. L'esempio sotto è UNA possibilità (web-app backend+frontend containerizzata) — sostituiscilo con il layout reale del tuo stack (una CLI, una lib, un monorepo, ecc. hanno strutture diverse).

```
# esempio (web-app full-stack) — non un default obbligato
nome-progetto/
├── docker-compose.yml        # se serve orchestrazione container
├── backend/
│   └── app/                  # models / routers / services / schemas
├── frontend/
│   └── src/                  # components / stores / services
└── CLAUDE.md
```

### 3. Modello Dati / Persistenza (se il progetto ha stato persistente)
Definisci le entità e come sono memorizzate: per un DB relazionale tabelle con colonne, tipi, vincoli, foreign key/relazioni, indici; per altri store (documenti, file, KV) l'equivalente. Salta se il progetto è stateless.

### 4. Interfaccia / API (se il progetto espone una superficie)
Il contratto verso l'esterno nella forma giusta: endpoint HTTP (tabella Metodo/Endpoint/Descrizione), comandi e flag di una CLI, API pubblica di una libreria, eventi/messaggi di un servizio.

### 5. Componenti Chiave
I moduli principali e le loro responsabilità, qualunque sia lo stack (frontend/backend, comandi/core, ecc.).

### 6. Flusso Autenticazione
Se serve auth, diagramma il flusso (OAuth, JWT, sessioni, token, chiavi). Salta se non applicabile.

### 7. Flusso Dati
Come i dati si muovono nel sistema per le operazioni chiave.

## Formato Output

Includi solo le sezioni pertinenti allo stack (ometti Modello Dati / API se non applicabili):

```markdown
# Scope: [Nome Progetto]

## Architettura
[Diagramma ASCII]

## Struttura Progetto
[Tree structure secondo lo stack]

## Modello Dati / Persistenza   (se ha stato)
[schema DB, o equivalente per lo store scelto]

## Interfaccia / API   (se espone una superficie)
[tabella endpoint, comandi CLI, API libreria, …]

## Componenti
[Lista con descrizioni]

## Flusso Auth (se applicabile)
[Diagramma o step]

## Prossimi Passi
- /write-plan per piano implementazione
```

## Avvia

Rivedi il contesto della discovery e crea il documento di scope tecnico. Se la discovery non è stata fatta, chiedi prima le informazioni necessarie.
