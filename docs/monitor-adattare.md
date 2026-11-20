# Adattare /monitor al tuo lavoro

/monitor smista quello che ti arriva. Arturo ne dà una versione di serie, uguale per tutti. Il tuo
lavoro però ha fonti, persone e priorità sue. Questa pagina dice come adattare /monitor senza
perdere gli aggiornamenti di Arturo, e come /monitor impara dalle tue correzioni.

Stato (17/11/2026): esistono il primo avvio, i ponti e il motore che impara (`bin/monitor/impara.py`).
Il giro quotidiano di serie arriva con una fase successiva.

## Chi tiene cosa

| Pezzo | Dove sta | Chi lo cambia |
|---|---|---|
| Il motore: schema delle righe, fingerprint, cursori, apprendimento | `bin/monitor/` in Arturo | gli aggiornamenti di Arturo |
| Le tue fonti in più | `~/.claude/personale/monitor/ponti.json` e i tuoi programmi | tu ([`monitor-ponti.md`](monitor-ponti.md)) |
| Le scelte sull'apprendimento | `~/.claude/personale/monitor/apprendimento.json` | tu |
| Un /monitor tutto tuo | una skill `monitor` nella tua Orsa, dichiarata in `personale/sostituzioni.txt` | tu, con Claude |
| Quello che /monitor ha imparato | `~/.claude/data/monitor/appreso.json` | il motore, col tuo sì o da solo se l'hai scelto |

Un aggiornamento di Arturo cambia solo la prima riga. Le altre stanno nella tua Orsa
([`strati.md`](strati.md)).

## Tre livelli di adattamento

1. **Di serie.** Usi `/monitor` di Arturo e scegli le fonti al primo avvio. Va bene per cominciare.
2. **Con le tue fonti.** Aggiungi un ponte tuo per una fonte che Arturo non legge (una chat di
   lavoro, un gestionale). Il resto resta di serie.
3. **Tutto tuo.** Scrivi una skill `monitor` nella tua Orsa: le tue fonti, le tue tabelle dei
   progetti, i tuoi freni, il tuo report. La dichiari in `personale/sostituzioni.txt` con il motivo
   dopo `#`. Il nome `/monitor` va alla tua, quella di Arturo resta `arturo:monitor`.

Al terzo livello il tuo /monitor usa comunque il motore di Arturo per imparare: chiama
`arturo monitor impara` coi segnali qui sotto. Così l'apprendimento migliora con gli aggiornamenti,
e i tuoi file restano tuoi.

## Come impara

Il ciclo ha quattro passi.

1. **Segnale.** Ogni correzione diventa una riga di `segnali.jsonl`: un todo scartato o rimesso in
   piedi, un todo che era già fatto, la proposta di un mittente nuovo accolta o rifiutata, una voce
   del report su cui hai agito. Li scrive `arturo monitor impara segna`, oppure un tuo ponte li
   consegna in un file e `arturo monitor impara raccogli` li importa.
2. **Calcolo.** `arturo monitor impara calcola` confronta i segnali con le soglie:
   - un mittente con una proposta accolta va da solo nei todo; con due rifiuti e nessuna accolta non
     torna fra le proposte;
   - una regola di scarto con due ripristini sugli ultimi cinque usi si sospende;
   - una sezione del report senza azioni negli ultimi cinque giri si comprime in una riga contata.
3. **Riga "Appreso".** Ogni modifica compare in testa al report, con il comando per annullarla.
   Di serie la modifica è una proposta e entra col tuo sì. Con `{"modo": "auto"}` in
   `apprendimento.json` entra da sola, e la riga la racconta lo stesso.
4. **Annullo.** `arturo monitor impara annulla <id>` riporta lo stato di prima. Le stesse prove non
   rifanno la modifica: serve un segnale nuovo.

Cosa il motore non fa mai:
- non nasconde una cosa con una cifra, una scadenza vicina o una domanda diretta: il segnale porta
  `--intoccabile` e non conta verso un "no" o una compressione;
- non comprime una sezione che hai messo in `"sempre"` (`{"sempre": ["scadenze"]}`);
- non scrive fuori da `~/.claude/data/monitor/`, e non legge i file di un /monitor personale.

## Un esempio vero

Il /monitor di chi mantiene Arturo è del terzo livello: legge più caselle di posta, una chat di
lavoro, le trascrizioni delle call e un gestionale, e scrive i todo in un database suo. Le sue
regole di scarto le distilla un subagent dai motivi degli scarti. Il motore gli serve per tre cose
che prima si perdevano:
- i ripristini di un item declassato, che sospendono la regola sbagliata;
- i mittenti accolti dalle proposte, che dalla volta dopo entrano da soli;
- le sezioni del report che nessuno apre, che si riducono a una riga.

Il suo `apprendimento.json` dice `{"modo": "auto", "sempre": ["scadenze", "fonti non lette"]}`.
