# Quale macchina, quale browser, quale profilo

Questo documento è per chi sviluppa Arturo. Unisce tre segnalazioni e due task che descrivono lo stesso
errore: Claude agisce sulla superficie sbagliata e non dice quale ha scelto. È la base delle funzioni
nuove dello step 9 del piano di novembre 2026 (#5881, #5692).

## Da dove viene

- **Segnalazione n. 44 (2/11/2026).** Con due Chrome collegati, i nomi "Browser 1" e "Browser 2" cambiano
  durante la sessione. Dopo l'errore "the Chrome extension disconnected mid-operation" la sessione torna
  da sola sull'altro Chrome, senza avviso. Il deviceId invece resta lo stesso per tutta la sessione.
- **Segnalazione n. 74 (13/11/2026), task #5600.** La persona chiede di cercare "via Chrome". Gli
  strumenti di Chrome non sono caricati, e Claude passa a un altro server MCP del browser senza chiedere.
  Poi cerca nel profilo Chrome personale, non in quello dell'organizzazione.
- **Segnalazione n. 75 (15/11/2026), task #5692.** Tre Chrome collegati, ognuno con un account Google
  diverso. Claude apre un Google Sheet di lavoro nel Chrome già attivo, e Google chiede un nuovo accesso.
  Prima i connettori Google avevano risposto "Permission denied" sui file del dominio di lavoro.
- **L'uso di chi mantiene Arturo (revisione del 17/11, proposte 4 e 11).** Sette volte in sette giorni ha corretto
  la macchina: "aprimelo su firefox macbook" (15/11), "Devi aprirli su macbook" (16/11). Il 12/11: "il
  chrome che devi usare è quello che c'è su questa macchina". Il 13/11: "Non so quale Chrome sia Browser 1".

## Cosa c'è già

- `output-styles/conciso.md` dice di ricordare il browser per deviceId, mai per nome. Dopo ogni
  "disconnected" Claude rilancia `list_connected_browsers` e, se `inUse` è cambiato, riseleziona il
  browser con `select_browser` e lo dice. Il banco è SG04 in `tests/test_segnalazioni_2026_11_02.py`.
- Lo stesso stile dice che dopo `/chrome` a sessione aperta gli strumenti arrivano solo con `/exit` e
  `claude --continue` (segnalazione n. 40).
- Manca tutto il resto: il browser nominato dalla persona, il profilo collegato, l'account Google e la
  macchina dove sta la persona.

## Le tre domande, in quest'ordine

Claude risponde alle tre domande prima di aprire una pagina o di pilotare un browser. La macchina viene
prima, perché browser e profili esistono solo su una macchina.

### 1. Quale macchina

1. Se la persona nomina una macchina nel messaggio, Claude usa quella.
2. Se la sessione è interattiva nel terminale di questa macchina, la persona sta qui: Claude usa questa.
3. Se la sessione è un job in background, un attach via ssh o una sessione remota, la macchina della
   sessione non dice niente. Un Mac acceso per un lavoro non vuol dire che la persona stia lì.
   Claude usa la macchina davanti, se un segnale la dice (step 9, #5881). Senza segnale chiede una volta
   e ricorda la risposta per la sessione. Il segnale è
   `python3 ~/.config/herdr-app/mods/arturo/volta_davanti.py leggi`: dice "questa", "un'altra" col nome
   `hc exec --on` per raggiungerla, o "ignota".

Chi usa Arturo su un solo computer resta sempre al punto 2: per lui non cambia niente.

### 2. Quale browser

Prima il ruolo, poi il nome.
- **Da leggere.** Una pagina che la persona guarda e basta si apre nel suo browser di consultazione, con
  `open` (macOS) o `start` (Windows). Il browser predefinito vale finché la persona non ne indica uno.
- **Da pilotare.** Click, login, caricamenti e moduli passano dagli strumenti del browser collegato,
  oggi Claude in Chrome. Vale anche se la persona dice "aprimela su Firefox": pilotare è un altro ruolo.

Quando la persona nomina un browser, Claude usa quello. Se gli strumenti non sono caricati, Claude
carica la skill di quel browser prima di ogni altra via. Un altro server MCP del browser vale solo con
il sì della persona, anche se le istruzioni di quel server dicono di preferirlo (segnalazione n. 74).
`list_connected_browsers` può dire "connesso" a estensione morta: la sonda vera è `tabs_context_mcp`.

### 3. Quale profilo e quale account

- Con più Chrome collegati, Claude sceglie per deviceId e descrive ogni browser da cosa mostra: le schede
  aperte, l'account del pulsante "Account Google". Il nome "Browser N" non identifica niente.
- Prima di cercare o modificare dati di un account (un Drive, un foglio, una casella), Claude controlla
  l'account collegato e lo dice in una riga. Se l'account è sbagliato, cambia browser prima di agire.
- Se un connettore Google risponde "Permission denied" su un file di un altro dominio, il connettore è
  collegato a un altro account. Claude passa al Chrome con l'account giusto, senza chiedere alla
  persona di ricollegare il connettore (segnalazione n. 75).
- Il login lo fa la persona, nel Chrome giusto. Claude non scrive password.

## Una riga che dice dove

Ogni volta che la scelta non è ovvia, Claude scrive una riga prima di agire: "Apro sul MacBook, in
Firefox" oppure "Uso il Chrome con l'account del lavoro". La riga costa poco e trasforma un errore
silenzioso in una correzione immediata. È la regola comune alle tre segnalazioni.

## Cosa diventa codice

| Pezzo | Tipo | Dove | Task |
|---|---|---|---|
| Browser nominato e riga dell'account | regola, nessuna funzione nuova | `output-styles/conciso.md` e banco accanto a SG04 | #5600 |
| Mappa profilo Chrome e account Google | funzione nuova, approvata il 17/11 | file locale in `~/.claude/data/browser/`, mai in telemetria | #5692 |
| Macchina davanti | fatta il 17/11 (Volta 709be18) | `volta_davanti.py` di Volta, regola in `output-styles/conciso.md` (SG05) | #5881 |

La regola di #5600 non aspetta lo step 9: non cambia il disegno e non aggiunge stato.

## Le decisioni per lo step 9

Chi mantiene Arturo ha approvato le tre raccomandazioni il 17/11/2026. Il codice parte da qui.

1. **Il segnale della macchina davanti.** Volta scrive su ogni macchina un file con la
   macchina dove la persona ha toccato tastiera o finestra per ultimo, e l'ora. La sessione lo legge prima
   di aprire. Senza Volta, o con il file più vecchio di 15 minuti, vale il punto 3: Claude chiede una volta.
2. **La mappa dei profili.** La mappa nasce solo dal sì della persona, la prima volta
   che Claude trova l'account giusto. Tiene il nome del profilo Chrome e il dominio dell'account, non
   l'indirizzo intero. Il deviceId resta un suggerimento: nessuno ha provato che regga fra due sessioni.
   Claude controlla l'account a ogni uso, anche con la mappa.
3. **Dove sta la mappa.** In `~/.claude/data/browser/`, fuori da git e fuori dalla
   telemetria. Un account è un dato personale: `/segnala` lo toglie già, e la mappa non lo aggiunge.
