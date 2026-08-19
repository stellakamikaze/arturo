---
description: Raccolta requisiti strutturata - intervista per capire cosa costruire
---

# Discovery Progetto

Conduci una discovery per un nuovo progetto o feature. L'obiettivo è capire cosa costruire abbastanza a fondo da poter poi definire scope e piano — attraverso una conversazione, non un modulo da compilare.

## Obiettivo

Uscire dalla discovery sapendo: **il problema** (cosa risolviamo, per chi, come si misura il successo), **i vincoli tecnici** (stack, pattern esistenti, integrazioni, scala, deploy, sicurezza), e **le priorità** (MVP vs v2, must-have vs nice-to-have, deadline). Questi sono i territori da coprire, non una sequenza obbligata.

Sul problema, spingi fino a due cose distinte: **cosa succede oggi che non va** e **cosa deve succedere invece**. La seconda va portata a un risultato osservabile — qualcosa che si possa guardare e dire "c'è" o "non c'è". «Migliorare le performance» non lo è; «la lista si apre in meno di un secondo con 10.000 righe» sì. Se l'utente non riesce ancora a formularlo, va bene: allora il primo obiettivo del progetto è determinarlo, e va scritto così.

## Come condurla

Guida tu la conversazione verso questi territori, scegliendo ordine e ritmo in base a cosa emerge. Segui i fili che l'utente apre invece di forzare un percorso fisso: se parlando del problema salta fuori un vincolo tecnico, esploralo lì. Raggruppa le domande dove ha senso (poche domande mirate insieme battono un interrogatorio a raffica), e adatta la profondità al progetto — un tool interno non ha gli stessi requisiti di scala di un servizio pubblico.

Lo spirito è **chiedere prima di assumere**: quando un requisito è ambiguo o stai per dare qualcosa per scontato, chiedi. Meglio una domanda in più che uno scope costruito su un'ipotesi sbagliata. Quando senti di aver coperto i tre territori con la profondità che il progetto merita, chiudi.

## Dopo la Discovery

Crea un documento di sintesi:

```markdown
# Discovery: [Nome Progetto]

## Problema
[1-2 frasi: cosa succede oggi che non va]

## Criteri di Successo
[cosa deve succedere invece — ogni criterio è un risultato osservabile, non un'intenzione:
si deve poter dire "c'è" o "non c'è" senza discutere]
- [ ] Criterio 1
- [ ] Criterio 2

## Decisioni Tecniche
- Stack: [scelte]
- Pattern: [scelte]

## Scope MVP
1. Feature A
2. Feature B

## Fuori Scope (v2)
- Feature X
- Feature Y

## Prossimi Passi
- /scope per documento tecnico dettagliato
- /write-plan per piano implementazione
```

## Avvia

Parti dal problema — cosa costruiamo e perché — e lascia che la conversazione ti porti attraverso gli altri territori.
