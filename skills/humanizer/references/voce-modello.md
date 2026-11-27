# Il modello del file della voce

Parte della skill `humanizer` (`../SKILL.md`): `/voce` compone `~/.claude/personale/humanizer.md` con
questo modello. Le quattro parti vanno in quest'ordine, con questi titoli: la skill le cerca per nome.
Le righe fra parentesi sono istruzioni per te e non entrano nel file.

```markdown
# La mia voce

## I miei testi

(Due o tre testi per tipo, scritti dalla persona, così come li ha dati. Sopra ognuno una riga col tipo.)

### Email
...

## Le mie regole

(Le righe confermate al Passo 4 di /voce, con le sue parole. Una regola per riga.)
- Virgolette: dritte.
- ...

## Per tipo di testo

(Solo dove un tipo si comporta in modo diverso dagli altri. Un tipo senza differenze non ha la sua riga.)

### Email
- ...

### CV e lettere
- ...

### Post
- ...

### Documenti
- ...

## Le mie correzioni

(Una riga per correzione, col prima e il dopo. Tre correzioni uguali diventano una regola.)
- Prima: "..." — Dopo: "..."
```

La riga delle virgolette c'è sempre: senza una scelta della persona, dice "dritte".
