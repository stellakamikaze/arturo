---
description: Costruisce la tua voce per i testi che mandi fuori (email, CV, post, documenti) - qualche testo tuo, cosa ci trovo, una prova, poi il file nella tua Orsa. Rilanciato, la approfondisce
argument-hint: "[il tipo di testo da aggiungere, per esempio: email] (opzionale)"
---

# La tua voce

Ogni testo che la persona manda fuori (un'email, un CV, una lettera, un post, una proposta) segue la
sua voce, mai le regole brevi delle risposte in chat. La voce sta nella sua Orsa, nel file
`~/.claude/personale/humanizer.md`, e la legge la skill `humanizer` prima di consegnare un testo.
Questo comando costruisce quel file con lei, o lo approfondisce.

Chi ti parla **potrebbe non essere una persona tecnica**. Parla semplice, una domanda per volta.
Non nominare file, sezioni o skill se lei non lo chiede: per lei è "la tua voce".

**Cosa dice la persona**: $ARGUMENTS

Il file è della persona. Lo scrivi solo dopo il suo sì, e un aggiornamento di Arturo non lo tocca mai.
**Mai un'altra persona come modello**: la voce si ricava dai testi di chi firma. Il nome di un'altra
persona entra solo se lei lo chiede, e allora lo scrivi con le sue parole.

## Passo 0 — C'è già una voce?

```bash
F=~/.claude/personale/humanizer.md
if [ -s "$F" ]; then echo "VOCE PRESENTE"; grep -n '^## ' "$F"; else echo "VOCE ASSENTE"; fi
```

- `VOCE ASSENTE`: vai al Passo 1.
- `VOCE PRESENTE`: leggi tutto il file e vai a "Se la voce c'è già".

## Passo 1 — Per cosa scrivi

Chiedi per cosa scrive più spesso con Arturo, con queste voci: email, CV e candidature, post,
documenti lunghi (proposte, relazioni, offerte). Può sceglierne più d'una. Se `$ARGUMENTS` nomina
già un tipo, parti da quello senza chiedere.

## Passo 2 — I tuoi testi

Per ogni tipo scelto, chiedi due o tre testi scritti da lei che le piacciono: incollati qui, o il
percorso di un file. Un testo scritto da altri, o riscritto da un'IA, non serve: diglielo e chiedine
un altro. Se un file è lungo, leggilo tutto.

## Passo 3 — Cosa ci trovo

Mostra cosa trovi nei suoi testi, una cosa per riga, con un esempio preso da lei accanto a ogni riga:
- quanto sono lunghe le frasi, e se alterna corte e lunghe;
- se dà del tu o del lei, e a chi;
- come apre e come chiude (saluti, firma);
- le parole che usa per legare le frasi;
- la punteggiatura: virgolette (dritte, basse o curve), lineette, punto e virgola, punti esclamativi;
- se usa elenchi, grassetto o emoji;
- cosa evita.

Dividi le righe per tipo di testo solo dove i tipi si comportano in modo diverso. Le virgolette le
chiedi sempre, anche se nei testi non ci sono: senza una sua scelta restano dritte.

## Passo 4 — Conferma punto per punto

Chiedi conferma riga per riga. Una riga che non le somiglia la togli. Una riga che corregge la scrivi
con le sue parole, non con le tue.

## Passo 5 — Una prova

Prendi un testo breve del tipo che usa di più (tre o quattro righe: un'email di risposta, l'attacco
di un post) e riscrivilo nella sua voce, con le regole confermate. Chiedile se suona suo. Se lo
corregge, la correzione entra nella parte `## Le mie correzioni`, con il prima e il dopo.

## Passo 6 — Il file

Componi il file col modello `~/.claude/skills/humanizer/references/voce-modello.md`: le quattro
parti, nell'ordine. Mostralo tutto, poi scrivi `~/.claude/personale/humanizer.md` solo dopo il suo sì.
Se la cartella `~/.claude/personale/` manca, creala. Dopo la scrittura, rileggi il file dal disco e
mostra le prime righe di ogni parte.

Chiudi con due righe: da adesso i testi che manda fuori seguono questa voce; quando corregge un testo
riscritto, Arturo le propone di aggiungere la correzione, e `/voce` rilanciato approfondisce.

## Se la voce c'è già

Non rifare l'intervista. Proponi un solo approfondimento alla volta, il primo che serve:
1. **Un tipo di testo che manca**: se `$ARGUMENTS` lo nomina, o se `## Per tipo di testo` non copre un
   tipo che lei usa. Fai i Passi 2-5 solo per quel tipo.
2. **Tre correzioni che dicono la stessa cosa**: proponi la regola in `## Le mie regole` al posto
   delle tre, con le sue parole.
3. **Le regole rilette**: mostra le regole una per riga e chiedi quali valgono ancora.

Un file nato prima di `/voce`, con tre parti, riceve la parte `## Per tipo di testo` solo col sì, e il
resto resta com'è. Mostra sempre la modifica prima di scriverla.
