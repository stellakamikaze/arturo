---
description: Proponi a chi mantiene Arturo una skill che hai scritto tu, perché arrivi a tutti - la ripulisci con Claude e parte solo dopo il tuo sì
argument-hint: "[nome della skill] (opzionale)"
---

# Proponi una tua skill

Una skill nata da te (con `/creaskill` o a mano) vive solo sul tuo computer. Se serve anche ad
altri, questo comando la porta a chi mantiene Arturo come proposta: lui la legge, la prova e,
se entra, esce per tutti in un aggiornamento, citata nelle `/novita` col numero della proposta.
È nata alla sera del Computer Club del 27/10/2026.

Chi ti parla **potrebbe non essere una persona tecnica**. Parla semplice, una domanda per volta.

**Cosa dice la persona**: $ARGUMENTS

## Passo 1 — Quale skill

Le skill tue, cioè quelle che non arrivano con Arturo:

```bash
python3 - <<'EOF'
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.claude/bin"))
import telemetria
di_arturo = telemetria.file_di_arturo() or set()
for skill in sorted((Path.home() / ".claude" / "skills").glob("*/SKILL.md")):
    if f"skills/{skill.parent.name}/SKILL.md" not in di_arturo:
        print(skill.parent.name)
EOF
```

Se la persona l'ha nominata, usa quella. Se ce n'è una sola, proponi quella. Se non ce n'è
nessuna, diglielo e proponi `/creaskill`. Una skill che arriva con Arturo non si propone: per
cambiarla serve `/segnala`.

## Passo 2 — Leggi e ripulisci

Leggi `~/.claude/skills/<nome>/SKILL.md` per intero, e i file in `references/` se ci sono.
Prepara una copia per tutti, senza cambiare l'originale. Togli o sostituisci con un segnaposto:

- nomi di persone, clienti, aziende, progetti privati;
- indirizzi email, numeri di telefono, indirizzi di casa o di ufficio;
- percorsi del suo computer (`/Users/...`, `C:\Users\...`): diventano `~/...`;
- chiavi, token, password, link privati.

Se la skill senza quei dati non regge più, dillo: forse è personale per natura, e va bene così.

## Passo 3 — La bozza

Scrivi la bozza in un file temporaneo, in questa forma:

```
Perché serve: <due o tre frasi della persona: il lavoro che fa, quante volte le è servita>

--- SKILL.md ---
<la copia ripulita>
```

Testo al massimo 15000 caratteri. Se la skill è più lunga, manda il solo `SKILL.md` e dillo
nel "Perché serve". Poi:

```bash
python3 ~/.claude/bin/arturo segnala prepara --tipo proposta --titolo "Skill proposta: NOME" --file BOZZA
```

`prepara` toglie i percorsi della home e si ferma se trova qualcosa che sembra un segreto.
Mostra alla persona l'anteprima intera, com'è stampata, e i dati che hai tolto.

## Passo 4 — Il sì, poi l'invio

Chiedi: "La mando a chi mantiene Arturo?". Esce solo il testo che ha letto: nessun file parte
da solo. Dopo il sì:

```bash
python3 ~/.claude/bin/arturo segnala invia --canale arturo --file PRONTA
```

Riferisci il numero dell'esito ("è la segnalazione n. 21") e dove seguirla:
`/segnala stato` dice se è arrivata e quando esce. Se il server non risponde, parte da sola
alla prossima sessione.

## Regole

- Mai inviare senza il sì sulla bozza mostrata. Una modifica al testo passa di nuovo da `prepara`.
- Mai mandare la skill originale: solo la copia ripulita.
- Un segreto trovato da `prepara` ferma tutto: toglilo dalla copia e rilancia `prepara`.
