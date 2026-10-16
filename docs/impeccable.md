# Impeccable: il design delle interfacce, dall'upstream

Arturo non porta una skill di design per le interfacce. Se fai siti, pagine o app, ti consigliamo
**Impeccable**, una skill pubblica di Paul Bakaus: [github.com/pbakaus/impeccable](https://github.com/pbakaus/impeccable),
licenza Apache-2.0. Arturo non la copia: la installi dall'upstream, così ricevi le sue versioni
nuove senza aspettare Arturo.

## Cosa fa

- Dà a Claude un vocabolario di design condiviso con te: comandi come `/impeccable audit`,
  `critique`, `polish`, `harden`, `layout`, `typeset`, `quieter`, `bolder`.
- `/impeccable init` scrive in `PRODUCT.md` i fatti del progetto (pubblico, scopo, vincoli,
  voce). I comandi successivi li leggono e non te li richiedono.
- Un motore di controlli fissi trova i difetti tipici delle interfacce generate: testo grigio su
  fondo colorato, schede dentro schede, sfumature viola, contrasti bassi. Questi controlli non
  usano il modello e non chiedono una chiave.

## Come si installa

Ti serve Node.js per l'installatore. Nella cartella del progetto scrivi:

```bash
npx impeccable install
```

L'installatore trova `~/.claude` e ti chiede se installare nel solo progetto o per tutti i
progetti. `/setup` te la propone nella fase 8c e la installa per tutti i progetti, senza domande:
`npx --yes impeccable install --providers=claude --scope=global`. Poi chiudi e riapri Claude Code. Nel progetto scrivi `/impeccable init`.

Per aggiornarla:

```bash
npx impeccable update
```

Le altre vie (copia manuale, sottomodulo git) sono nel README dell'upstream, sezione
«Installation».

## Da sapere

- Se la installi per tutti i progetti, la cartella `~/.claude/skills/impeccable/` non è di
  Arturo. Git la vede come una cartella non tracciata e `/aggiorna` non la tocca.
- Non modificare a mano i file di Impeccable: il prossimo aggiornamento li sostituisce. Le tue
  scelte di progetto stanno in `PRODUCT.md` e `DESIGN.md`, nel progetto.
- L'agente `ui-ux-consultant` di Arturo fa una revisione dell'interfaccia leggendo il codice.
  Impeccable invece guida il lavoro di design e prova la pagina vera. Puoi usarli insieme.
