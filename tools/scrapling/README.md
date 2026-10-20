# scrape — leggere una pagina web senza browser

`scrape` legge UNA pagina di cui hai l'indirizzo e tiene solo ciò che serve: il markdown del
contenuto principale, il testo, o i soli nodi di un selettore CSS. Gira da Bash con
[Scrapling](https://github.com/D4Vinci/Scrapling) in un venv tutto suo: niente browser, niente
token di protocollo.

    scrape <url> [--md|--text|--html|--json] [--full] [--sel CSS] [-o FILE] [-q]

## Installazione (facoltativa)

Pesa circa 300 MB. La propone `/setup`, oppure:

    bash ~/.claude/tools/scrapling/setup.sh
    bash ~/.claude/tools/scrapling/banco.sh

Serve Python 3.10 o più recente (oppure `uv`, che lo scarica da solo). Il venv resta in
`tools/scrapling/.venv/` e non entra mai nel repository. Per toglierlo: cancella quella cartella.

## Quale strumento per leggere il web

Si sale di un gradino solo quando quello sotto non basta:

1. **Un'API o una CLI** del servizio, se esiste.
2. **`scrape`** per una pagina pubblica di cui hai l'indirizzo.
3. **Il browser** (per esempio l'estensione Claude in Chrome) per un login, un clic, o un sito che
   blocca le richieste automatiche.

## Opzioni

    --md         markdown del solo contenuto principale (default)
    --full       markdown della pagina intera, menu e piè di pagina compresi
    --text       testo nudo
    --html       HTML grezzo: non stamparlo a schermo, scrivilo su file
    --json       risposta JSON
    --sel CSS    estrae solo i nodi che corrispondono, per esempio --sel "h2,h3"
    -o FILE      scrive su file invece che a schermo
    -q           niente righe di stato

Con `-o FILE` il contenuto non entra nel contesto: lo scrivi su disco e poi cerchi lì dentro.
È il modo giusto per le pagine grandi. Ordini di grandezza su una pagina di bandi: l'HTML grezzo
pesa circa 100 KB, il markdown del contenuto 12 KB, i soli titoli con `--sel` meno di 1 KB.

## Quando il sito blocca

`scrape` fa una sola richiesta HTTP e si presenta per quello che è: un programma, non un browser.
Non finge di essere Chrome e non prova a superare le verifiche anti-bot. Se il sito risponde 401,
403, 429, 503 o una pagina di verifica ("Just a moment…", "Verifying you are human"), `scrape`
esce con 3 e consiglia di aprire la pagina nel browser.

| Exit | Significato |
|------|-------------|
| `0` | pagina letta |
| `2` | la pagina non c'è o il server è guasto (404, 5xx): il browser non cambierebbe l'esito |
| `3` | il sito blocca le richieste automatiche: apri la pagina nel browser |
| `4` | errore di rete |

Rispetta i termini d'uso del sito: `scrape` serve a leggere pagine pubbliche, non a scaricarne
grandi volumi o a passare un paywall.

## Banco

`banco.sh` gira senza rete: un server locale serve una pagina vera, una pagina di verifica, un 403
e un 404, e controlla che `scrape` mandi un user agent onesto e nessun referer. Rilancialo prima di
cambiare le frasi di `CHALLENGE` o la tabella `BLOCCO` in `scrape.py`.

## Gotcha di Scrapling

- `markdown` è un metodo, non una proprietà: `markdown(css_selector=None, main_content_only=False)`.
  Richiede `markdownify`, che l'extra `[fetchers]` non installa: `setup.sh` lo aggiunge.
- `Fetcher` di default finge di essere Chrome. `scrape.py` lo spegne con `impersonate=None` e
  `stealthy_headers=False`.
- `scrapling install` scarica i browser per il livello stealth: `scrape` non li usa, e `setup.sh`
  non lo lancia.
