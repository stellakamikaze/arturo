---
description: Crea una skill tua - quattro domande, una per volta, poi la skill in ~/.claude/skills/ che Claude usa da solo quando la richiesta torna
argument-hint: "[il lavoro che vuoi trasformare in skill] (opzionale)"
---

# Crea una skill

Una skill è un file di istruzioni che Claude apre da solo quando la richiesta della persona
gli somiglia. Serve per un lavoro che torna: una lettera che scrive ogni mese, un controllo
che fa sempre allo stesso modo, un formato che vuole sempre uguale. Invece di rispiegarlo ogni
volta, lo spiega una volta sola.

Chi ti parla **potrebbe non essere una persona tecnica**. Parla semplice, una domanda per volta,
e non nominare YAML, frontmatter o trigger: sono affari tuoi.

**Cosa dice la persona**: $ARGUMENTS

## Passo 1 — Quattro domande

Parti da quello che la persona ha già detto, in `$ARGUMENTS` o prima nella sessione: non
chiedere di nuovo una cosa che sai. Le domande, una per volta:

1. **Cosa deve fare?** Il lavoro in una o due frasi.
2. **Con quali parole lo chiederai?** Due o tre frasi vere, come le scriverebbe. Sono loro a
   far partire la skill.
3. **Un esempio vero.** Cosa ti dà all'inizio (un file, un testo, un nome) e cosa vuole alla
   fine. Se ha un risultato già fatto che le piace, fattelo indicare: vale più di dieci regole.
4. **Cosa NON deve fare?** Un lavoro che le somiglia ma è un altro, un errore che non vuole
   rivedere, un limite (per esempio "non mandare niente, prepara solo").

Se un lavoro così lo fa già un comando di Arturo o una skill che c'è, diglielo prima di
continuare: forse basta quello.

## Passo 2 — Il nome e dove va

Proponi un nome corto, in minuscolo con i trattini, che dica il lavoro (`lettera-mensile`,
`controllo-fatture`). Prima controlla che sia libero:

```bash
NOME="nome-proposto"
ls -d ~/.claude/skills/"$NOME" ~/.claude/commands/"$NOME".md 2>/dev/null && echo "OCCUPATO" || echo "libero"
```

Con `OCCUPATO` scegli un altro nome. Evita anche i nomi generici (`posta`, `scrivi`, `report`):
se un giorno Arturo porta una skill con lo stesso nome, il prossimo `/aggiorna` va in conflitto.
Un nome che dice il lavoro della persona non corre questo rischio.

Poi guarda dove finisce. `/fine` salva la skill nel repository della config della persona, se
ne ha uno. Se il repository non risulta privato, `/fine` la tiene sulla macchina e chiede prima
di pubblicarla:

```bash
git -C ~/.claude remote get-url origin 2>/dev/null && gh repo view "$(git -C ~/.claude remote get-url origin)" --json visibility -q .visibility 2>/dev/null
```

Se risponde `PUBLIC`, o se la visibilità non si legge, dillo alla persona prima di scrivere:
`/fine` le chiederà se pubblicarla, e se dice sì nella skill non vanno nomi di clienti,
indirizzi, cifre o altro che non vuole rendere pubblico.

## Passo 3 — La skill

Mostra alla persona il testo che scriverai, poi col suo sì scrivi
`~/.claude/skills/<nome>/SKILL.md`:

```markdown
---
name: <nome>
description: >-
  <cosa fa, in una frase>
when_to_use: >-
  Usa quando la persona dice "<frase 1>", "<frase 2>", "<frase 3>". NON per <il lavoro simile
  che è un altro>.
---

# <Il lavoro, in parole sue>

## Che cosa deve uscire

<Il risultato buono, descritto: com'è fatto, per chi è, perché è fatto così. L'esempio vero
del Passo 1, se c'è.>

## Cosa non fare

<I limiti del Passo 1, ognuno col suo perché.>
```

Il corpo descrive un buon risultato e il perché, non una procedura passo per passo: così Claude
sceglie la strada da solo, e la skill regge anche quando il caso cambia un po'. Il `when_to_use`
è la parte che conta di più: Claude decide se aprire la skill leggendo solo quello. Se servono
parti lunghe (un modello, un elenco di nomi), mettile in file a parte nella cartella
`references/` della skill e citale dal corpo.

## Passo 4 — La prova

```bash
bash ~/.claude/skills/system-audit/audit.sh 2>&1 | grep -iE "skill|fantasma|peso|FAIL" | head -20
```

Nessun FAIL sulla skill nuova. Poi la prova vera, che fa la persona: apre una sessione nuova
di Claude Code e scrive una delle frasi del Passo 1. Se Claude non apre la skill, riscrivi il
`when_to_use` con le parole che ha usato davvero, e riprova.

## Passo 5 — Per chi vuole di più

Se la skill diventa importante, la skill ufficiale `skill-creator` di Anthropic (nel
marketplace `claude-plugins-official`) la mette alla prova su molte richieste e migliora il
`when_to_use` con i numeri. Proponila solo se la persona vuole andare oltre: richiede tempo.

## Regole

- Una skill fa un lavoro solo. Se la persona ne descrive due, ne fai due.
- Non modifichi le skill di Arturo per fare spazio a quella nuova: la sua sta nella sua cartella.
- Niente password, token o chiavi nella skill. Se il lavoro ne usa uno, la skill dice dove
  trovarlo, mai il valore.
