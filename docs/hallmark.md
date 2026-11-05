# Hallmark: le pagine nuove, dall'upstream

Arturo non porta una skill che costruisce pagine. Se fai siti o pagine nuove, ti consigliamo
**Hallmark**, una skill pubblica di Together AI: [github.com/nutlope/hallmark](https://github.com/nutlope/hallmark),
licenza MIT. Arturo non la copia: la installi dall'upstream, così ricevi le sue versioni nuove
senza aspettare Arturo. Lavora insieme a Impeccable (`docs/impeccable.md`), non al suo posto.

## Cosa fa

- Costruisce da zero una pagina che non sembra generata. Sceglie un tema da un catalogo di
  cinquanta, e due pagine nello stesso tema escono diverse.
- Parte da cosa viene a fare il visitatore (prenotare, comprare, iscriversi) e mette l'azione
  dove la mettono i siti veri di quel settore.
- Non inventa numeri, citazioni o loghi. Senza le tue foto usa foto con licenza aperta, con il
  credito nella pagina, in spazi che le tue foto sostituiscono dopo.
- Controlla la pagina su otto larghezze di schermo con `sloplint --render`, poi la fa rivedere a
  un subagent che non ha visto il lavoro.

## Con Impeccable

Le due skill lavorano in catena. Impeccable guida, Hallmark costruisce le pagine nuove:

```
impeccable context, sempre per primo
  +-- pagina esistente, rifinitura, app, dashboard, documentazione  --> Impeccable
  +-- pagina NUOVA da convincere o da mostrare                      --> Hallmark la costruisce
        --> impeccable document scrive DESIGN.md --> le rifiniture tornano a Impeccable
verifica finale di una pagina: impeccable audit più sloplint --render di Hallmark
```

- `DESIGN.md` lo scrive solo `/impeccable document`. Hallmark lo legge come sistema già deciso.
  Non usare il suo "lock the system": scrive un altro formato nello stesso file.
- Su una pagina fatta con Impeccable, `sloplint` è solo una segnalazione: vincono le tue scelte e
  il `DESIGN.md` del progetto.
- Claude segue la catena se la trova nel tuo `~/.claude/CLAUDE.md`. `/setup` te la propone nella
  fase 8c e la scrive solo dopo il tuo sì.

## La regola per il tuo CLAUDE.md

Con tutte e due installate, questa riga in fondo a `~/.claude/CLAUDE.md` fa lavorare le skill in catena:

> Design delle interfacce: impeccable guida, hallmark costruisce le pagine nuove. Ogni lavoro parte da `impeccable context`; una pagina nuova da convincere o da mostrare la costruisce hallmark, poi impeccable `document` scrive DESIGN.md e guida le rifiniture; il resto è di impeccable. Verifica finale: impeccable `audit` più hallmark `sloplint --render`.

## Come si installa

Ti serve Node.js. In qualunque cartella scrivi:

```bash
npx --yes skills add nutlope/hallmark -g -a claude-code --copy -y
```

`-g` la installa per tutti i progetti, `--copy` mette file veri in `~/.claude/skills/hallmark/`
invece di un collegamento. Poi chiudi e riapri Claude Code. Per aggiornarla rilancia lo stesso
comando.

## Da sapere

- La cartella `~/.claude/skills/hallmark/` non è di Arturo. Git la vede come una cartella non
  tracciata e `/aggiorna` non la tocca.
- Non modificare a mano i file di Hallmark: il prossimo aggiornamento li sostituisce.
- Hallmark ha un hook facoltativo, `scripts/install-hook.mjs`, che scrive in `settings.json` e
  controlla ogni file che Claude modifica. Arturo non lo installa: Impeccable ha già il suo.
- Le immagini generate con Together AI partono solo se imposti `TOGETHER_API_KEY`. Senza la
  chiave Hallmark usa le tue foto o quelle della sua libreria.
- Per fotografare il tuo prodotto, Hallmark può avviare il server di sviluppo del progetto. Lo
  fa nella cartella del progetto, con i pacchetti che il progetto stesso dichiara.
