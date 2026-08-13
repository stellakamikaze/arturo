---
description: Verifica completezza strutturale (wrapper sull'agente structural-completeness-reviewer)
---

# Arewedone

Wrapper sottile sull'agente `structural-completeness-reviewer`. Il grosso della logica sta
nell'agente — qui non la duplichiamo.

**Quando usarlo standalone**: dopo un refactoring o una feature multi-layer, quando vuoi la sola
verifica di completezza strutturale senza chiudere la sessione. (Dentro `/fine` gira già in
automatico, quindi non serve invocarlo prima o dopo `/fine`.)

## Cosa fa

1. Lancia l'agente `structural-completeness-reviewer`: cambiamenti integrati, dead code rimosso,
   nessun debito tecnico introdotto, integrità strutturale, conformità alle convenzioni.
2. Consolida i risultati per severità e li presenta raggruppati:
   - **AUTO-FIX** (meccanici: import orfani, dead code ovvio, console.log) → applica dopo conferma rapida.
   - **ASK** (cambiano comportamento o ambigui) → attendi decisione esplicita.

   NON applicare fix senza mostrare prima cosa verrà modificato.
3. Se ci sono modifiche completate, chiudi con `/commit`.
