---
description: Crea una skill tua - cinque domande, una per volta, poi la skill in ~/.claude/skills/ che Claude usa da solo quando la richiesta torna
argument-hint: "[il lavoro che vuoi trasformare in skill, o il nome di una skill che hai già] (opzionale)"
---

# Crea una skill

Una skill è un file di istruzioni che Claude apre da solo quando la richiesta della persona
gli somiglia. Serve per un lavoro che torna: una lettera che scrive ogni mese, un controllo
che fa sempre allo stesso modo, un formato che vuole sempre uguale. Invece di rispiegarlo ogni
volta, lo spiega una volta sola.

Chi ti parla **potrebbe non essere una persona tecnica**. Parla semplice, una domanda per volta,
e non nominare YAML, frontmatter o trigger: sono affari tuoi.

**Cosa dice la persona**: $ARGUMENTS

## Se la skill c'è già

Se la persona scrive il nome di una skill, o parla di una skill che ha già, guarda prima com'è:

```bash
python3 "${ARTURO_CODICE:-$HOME/.claude}/bin/skill_sezioni.py" stato "nome-della-skill"
```

- `ASSENTE`: è un lavoro nuovo, vai al Passo 1.
- `ARTURO`: è una skill di Arturo e non si tocca. Le sue regole la persona le aggiunge in
  `~/.claude/personale/<nome>.md`; un difetto va a chi mantiene Arturo con `/segnala`.
- `COMPLETA`: ha già "Finito quando" e "Attrezzi". Dillo e fermati. Se la persona vuole cambiare
  la lista, la correggi con lei riga per riga.
- `MANCA|<sezioni>`: la skill è nata prima delle due sezioni e funziona. Non rifare le domande da
  1 a 4 e non toccare il resto del file. Leggi il suo `SKILL.md`, poi fai solo la domanda 5 del
  Passo 1; se manca solo "Attrezzi", nessuna domanda. Mostra le sezioni che aggiungi, con i titoli
  e la forma del Passo 3, e dopo il sì scrivile in fondo al file. Se nella cartella della skill ci
  sono già script o modelli, "Attrezzi" nasce con una riga per ognuno: il file e quando si usa.
  Chiudi col controllo del Passo 4, senza la prova in una sessione nuova.

## Passo 1 — Cinque domande

Parti da quello che la persona ha già detto, in `$ARGUMENTS` o prima nella sessione: non
chiedere di nuovo una cosa che sai. Le domande, una per volta:

1. **Cosa deve fare?** Il lavoro in una o due frasi.
2. **Con quali parole lo chiederai?** Due o tre frasi vere, come le scriverebbe. Sono loro a
   far partire la skill.
3. **Un esempio vero.** Cosa ti dà all'inizio (un file, un testo, un nome) e cosa vuole alla
   fine. Se ha un risultato già fatto che le piace, fattelo indicare: vale più di dieci regole.
4. **Cosa NON deve fare?** Un lavoro che le somiglia ma è un altro, un errore che non vuole
   rivedere, un limite (per esempio "non mandare niente, prepara solo").
5. **Come capisci che è venuto bene?** Le tre o quattro cose che guarda lei prima di dire "va
   bene": i conti tornano, c'è la data, sta in una pagina. Diventano la lista che Claude
   controlla da solo prima di consegnare.

Se dopo le cinque risposte non sai ancora fare il lavoro senza chiederle altro, continua con
una domanda per volta sul punto che manca. Ti fermi quando lo sai fare da solo.

Se un lavoro così lo fa già un comando di Arturo o una skill che c'è, diglielo prima di
continuare: forse basta quello.

## Passo 2 — Il nome e dove va

Proponi un nome corto, in minuscolo con i trattini, che dica il lavoro (`lettera-mensile`,
`controllo-fatture`). Prima controlla che sia libero:

```bash
NOME="nome-proposto"
# Le skill e i comandi della persona, poi quelli di Arturo: col plugin stanno nella sua cartella.
ESITO=libero
for P in ~/.claude/skills/"$NOME" ~/.claude/commands/"$NOME".md "${ARTURO_CODICE:-$HOME/.claude}/skills/$NOME"; do
  [ -e "$P" ] && ESITO=OCCUPATO
done
echo "$ESITO"
```

Con `OCCUPATO` scegli un altro nome; se la persona voleva sistemare proprio quella skill, torna a
"Se la skill c'è già". Evita anche i nomi generici (`posta`, `scrivi`, `report`):
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
  Usa quando la persona dice "<frase 1>", "<frase 2>", "<frase 3>". Non per <il lavoro simile
  che è un altro>.
---

# <Il lavoro, in parole sue>

## Che cosa deve uscire

<Il risultato buono, descritto: com'è fatto, per chi è, perché è fatto così. L'esempio vero
del Passo 1, se c'è.>

## Cosa non fare

<I limiti del Passo 1, ognuno col suo perché.>

## Finito quando

<Le risposte alla domanda 5, una per riga, ognuna controllabile con un sì o un no. Prima di
consegnare Claude le controlla tutte e dice l'esito di ognuna.>

## Attrezzi

<Nasce vuota. Ogni script o modello che Claude costruisce per questo lavoro e che serve anche
la volta dopo va nella cartella della skill, con una riga qui: il file e quando si usa.>
```

Il corpo descrive un buon risultato e il perché, non una procedura passo per passo: così Claude
sceglie la strada da solo, e la skill regge anche quando il caso cambia un po'. Il `when_to_use`
è la parte che conta di più: Claude decide se aprire la skill leggendo solo quello. Se servono
parti lunghe (un modello, un elenco di nomi), mettile in file a parte nella cartella
`references/` della skill e citale dal corpo. "Finito quando" è la sola lista: la persona la
legge e la corregge, e Claude non consegna finché una riga dice no.

## Passo 4 — La prova

```bash
bash ~/.claude/skills/system-audit/audit.sh 2>&1 | grep -iE "skill|fantasma|peso|FAIL" | head -20
```

Nessun FAIL sulla skill nuova. Rileggi il file scritto: ha le quattro sezioni ("Che cosa deve uscire",
"Cosa non fare", "Finito quando", "Attrezzi"), e a ogni riga di "Finito quando" si risponde sì o no.
Poi la prova vera, che fa la persona: apre una sessione nuova
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
