---
description: Crea piano implementazione step-by-step da scope - task ordinati, dipendenze, strategia test
---

# Piano Implementazione

Crea un piano di implementazione concreto basato sullo scope completato. Questo piano definisce l'ORDINE di implementazione con step chiari e actionable.

## Prerequisiti

Questo comando va eseguito DOPO `/scope`. Se non esiste scope nella conversazione, chiedi di eseguire `/scope` prima o fornisci:
- Architettura tecnica
- Lista feature MVP
- Decisioni stack

## Principi di Planning

1. **Vertical slices**: Implementa feature-by-feature, non layer-by-layer
2. **Test early**: Setup infrastruttura test prima
3. **Foundation first**: Auth, DB, API base prima delle feature
4. **Valore incrementale**: Ogni step produce qualcosa di testabile

## Struttura Piano

Deriva le fasi dallo scope e dallo stack reale del progetto. La progressione tipica è: **Setup → Foundation → Core Features → Integration → Deploy Ready**, ma cosa contiene ogni fase dipende dal progetto — non forzare layer che non esistono.

L'esempio sotto è per una web-app full-stack (backend + DB + frontend); adattalo. Per una CLI, una libreria, uno script dati, un servizio senza UI, un'estensione, ecc. le fasi restano ma i task cambiano: niente "scaffold frontend" se non c'è frontend, niente "migrations" se non c'è database.

### Fase 0: Setup Progetto
- [ ] Struttura progetto (secondo lo stack scelto)
- [ ] Ambiente di sviluppo / build / packaging (Docker, venv, toolchain — quello che serve)
- [ ] Configurazione ed eventuali variabili ambiente
- [ ] CLAUDE.md per il progetto

### Fase 1: Foundation
Le fondamenta su cui poggiano le feature. A seconda del progetto: persistenza dati + migrations, API/interfaccia base, autenticazione, scaffold UI, entry point CLI, contratto pubblico della libreria.

### Fase 2: Core Features (MVP)
Suddividi ogni feature nei suoi tagli verticali (es. per una web-app: backend model+endpoint / frontend componente+integrazione / test; per una CLI: comando+logica / test). Ogni feature deve chiudersi con una verifica.

### Fase 3: Integration
- [ ] Connetti le feature tra loro
- [ ] Test end-to-end del flusso reale
- [ ] Error handling
- [ ] Rifinitura (UI o UX del tool)

### Fase 4: Deploy Ready
- [ ] Configurazione ambienti / distribuzione
- [ ] Security review
- [ ] Documentazione

## Formato Output

Esempio per una web-app full-stack — adatta i tagli di ogni feature allo stack reale (Backend/Frontend qui sotto sono solo un caso; per una CLI sarebbe Comando/Test, ecc.):

```markdown
# Piano: [Nome Progetto]

## Fase 0: Setup
- [ ] Task 1
- [ ] Task 2

## Fase 1: Foundation
- [ ] Task 1 (dipende da: Fase 0)
- [ ] Task 2

## Fase 2: Core Features

### Feature A: [Nome]
- [ ] Backend: [task specifico]
- [ ] Frontend: [task specifico]
- [ ] Test: [come verificare]

### Feature B: [Nome]
- [ ] Backend: [task specifico]
- [ ] Frontend: [task specifico]
- [ ] Test: [come verificare]

## Fase 3: Integration
- [ ] Task 1
- [ ] Task 2

## Strategia Test
- Unit test: [approccio]
- Integration test: [approccio]
- Test manuali: [flow chiave]

## Prossimo Step
- Inizia con Fase 0, Task 1
```

## Avvia

Rivedi il documento di scope e crea un piano di implementazione ordinato. Ogni task deve essere concreto e actionable. Se lo scope non è stato fatto, chiedi prima le informazioni necessarie.
