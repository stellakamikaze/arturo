# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

HTML e CSS statici, nessun framework, nessuna dipendenza di build. Sorgente in `sito/`, configurazione del server in `server/`. Pubblica dal 16/10/2026, senza parola d'ordine (decisione di Federico: «togli l'accesso via parola d'ordine»); prima era dietro una parola d'ordine condivisa (1/10/2026). `/admin/` resta dietro Cloudflare Access.

## Users

Visitatore principale: **chi conosce già l'IA e la usa in chat** (ChatGPT, Claude) ma non ha mai usato un terminale (decisione di Federico, 15/10/2026). Primo utente reale: una persona non tecnica, dal 16/9/2026.

Casi d'uso, in quest'ordine: il lavoro cognitivo e della conoscenza (scrivere e revisionare, ricerca e sintesi, posta e progetti, archivio e documenti), poi i piccoli strumenti su misura per un caso d'uso specifico. Le organizzazioni (studio, redazione, associazione) hanno una pagina a sé, `sito/organizzazioni/`: nella home resta solo un rimando.

## Product Purpose

Arturo è un harness per Claude Code: guardie di sicurezza, sessioni che si aprono e si chiudono in ordine, agenti, skill e un curriculum dei principi. Gratuito, open source (MIT), in italiano. Successo: chi parte da zero lo installa con `/setup` e lavora senza fare danni irreversibili.

## Positioning

Estratto da una configurazione usata ogni giorno in produzione, igienizzato. Bene comune prima, contatti come effetto (decisione del 16/9/2026). Dice apertamente cosa non è neutro: Claude Code è un servizio a pagamento di un'azienda privata, ogni aggiornamento è codice di altri che gira sul tuo computer, e Arturo manda dati d'uso a chi lo mantiene, accesi di default.

## Operating Context

Terminale e Claude Code. Installazione: `git clone https://github.com/stellakamikaze/arturo.git ~/.claude`, poi `/setup`. Ciclo: `/inizio`, lavoro, `/fine`. Aggiornamenti: automatici alla chiusura della sessione, solo rilasci con tag firmati (dal 16/10/2026, decisione di Federico: «update automatico è acceso di default»); avviso nella barra in basso; `/aggiorna` per guardare prima, `/aggiorna indietro` per tornare. Curriculum in `docs/principi/`, novità in `NOVITA.md` raccontate da `/novita`. Nove comandi in vetrina: `/inizio`, `/fine`, `/aggiorna`, `/novita`, `/segnala`, `/setup`, `/guidami`, `/diagnosi`, `/creaskill`. Lo sparring lo apre Claude.

## Capabilities and Constraints

- 23 guardie e automazioni, 10 comandi (nove in vetrina, più lo sparring che Claude apre da solo), 9 agenti, 4 skill (README di main al 16/10/2026, v2026-10-16.4: vanno riletti dal README prima di citarli). Lo strato delle organizzazioni, il percorso a tappe, `/progetto`, `/discovery` e `/write-plan` sono usciti il 16/10/2026: lo strato torna più avanti, rifatto.
- Impegni del README: repository pubblico e MIT, aggiornamenti automatici solo con rilasci firmati e spegnibili (`arturo aggiornamenti manuali`), telemetria minima accesa di default con il perché, Arturo in italiano, stop dichiarato.
- La telemetria è centrale nel racconto: Arturo impara da come lo usi. Accesa di default, si spegne con `arturo telemetria spegni`, `ARTURO_TELEMETRIA=0` o `DO_NOT_TRACK=1`. Escono solo eventi da un elenco chiuso con un id di installazione casuale e stabile (sulla pagina non si scrive che i dati sono senza nome: l'id resta lo stesso nel tempo), mai testi, file o nomi. La pagina dice cosa esce, cosa no, come si spegne e come i dati diventano correzioni.
- Firma solo «Progetto di Federico Nejrotti» (decisione del 15/10/2026). Nessuna cifra, nessun prezzo. L'affiancamento a pagamento non compare finché la sua forma non è decisa.
- La pagina conta le visite con Plausible, ospitato da chi mantiene Arturo e servito dal dominio della landing (decisione di Federico, 15/10/2026: «implementa Plausible»). Niente cookie, niente tracker di terzi, nessun font da server esterni, e il piede lo dice. La telemetria riguarda Arturo sul computer di chi lo usa, non il sito.
- La home porta gli articoli sull'IA di stellakamikaze.org e l'iscrizione alla sua newsletter (decisione di Federico, 15/10/2026). Il modulo di Ghost è copiato in `sito/vendor/`, non caricato da un CDN.

## Brand Commitments

- Nome: **Arturo**. Da Arktouros, «il guardiano dell'orsa», la stella dei naviganti.
- Figura: **la stella Arturo** che segue l'Orsa e veglia sui naviganti (dal 1/10/2026; il maggiordomo custode è uscito il 30/9).
- Firma: «progetto di Federico Nejrotti». Voce: italiano semplice, diretto, onesto sui limiti.
- Identità visiva propria di Arturo, separata dal canone SK di Federico.
- Registro: landing di prodotto delle IA, accanto a Ghost AI, Steel.dev e Save.design (preferenza di Federico, 15/10/2026: «vorrei più una landing page di prodotto»). La stella resta nel marchio e nel reticolo del cielo.

## Evidence on Hand

README.md, NOVITA.md, docs/principi/00 e 01, commands/*.md. Nessuna testimonianza, nessun cliente: non inventarne. I numeri d'uso esistono, ma restano privati a chi mantiene Arturo: la pagina non ne cita.

## Product Principles

1. Chi non programma deve capire e installare senza aiuto.
2. Onestà prima della persuasione: i limiti si dicono nella stessa pagina dei benefici.
3. Nessuna promessa che il codice non mantiene.
