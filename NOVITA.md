# Novità

Questo file è il canale di aggiornamento di Arturo. Ogni volta che l'harness evolve in un
modo che vale la pena raccontare, qui compare una entry: cosa cambia, il principio dietro,
a chi serve. La entry più recente sta in cima, con data ISO nell'intestazione. Una correzione nata
da una segnalazione la cita con la forma "segnalazione n. X" o "proposta n. X": `/segnala stato` la
riconosce così.

Non serve leggerlo a mano: dopo un `git pull`, all'avvio della sessione Arturo ti avvisa se
c'è qualcosa che non hai ancora visto, e `/novita` te lo racconta in parole semplici,
con la possibilità di fare sparring (`/sparring`) per capire se la novità serve al tuo
modo di lavorare.

---

## 2026-11-09 — Guardie, /monitor e controlli: le correzioni del lotto L10

**Cosa cambia**:
- La guardia blocca di nuovo `bw export` e `mkfs` dentro `$(...)` e i backtick, anche fra virgolette doppie:
  bash li esegue. Il lotto L2 li aveva lasciati passare.
- Un file dentro `hooks/` di un tuo mod personale resta protetto, ma il messaggio dice che è il tuo mod e,
  nello stesso passo, come caricarlo con `CLAUDE_CODE_PLUGIN_DIRS` (segnalazione n. 63).
- /monitor: una riga con un carattere di separazione Unicode non si spezza più, una lettura dichiarata intera
  con meno elementi letti si scarta, una fonte scelta che non consegna niente si vede (`righe.py --attese`), e
  due ponti Google insieme non danno più ogni email due volte. Un `cursori.json` rotto non si riscrive.
- Il gate dei progetti fa girare anche pytest in un progetto node con `requirements.txt`, e non dà più rosso
  per lo script di test di `npm init`, per un TypeScript non installato o per un `--dir` relativo.
- `arturo todo --help` dà l'aiuto, e una cartella personale che è un repository non diventa un progetto.
- Il controllo degli aggiornamenti all'avvio non lascia più un `git fetch` appeso per sempre; alla chiusura
  il ripristino del titolo del Terminale non aspetta più un permesso di macOS.
- `setup.sh` di scrape si può rilanciare, e dice "già installato" solo se i pacchetti ci sono davvero.

**Il principio**: un controllo che dice "rosso" per uno strumento che manca, o "verde" perché non ha guardato,
fa perdere fiducia a tutti i controlli.

## 2026-11-09 — L'aggiornamento automatico non aspetta più i processi di servizio di Claude Code

**Cosa cambia**:
- Claude Code dalla 2.1.31x tiene accesi alcuni processi di servizio: il daemon delle sessioni in background e
  le sessioni di riserva (`bg-spare`, `bg-pty-host`). Arturo li contava come sessioni aperte, e un rilascio si
  rinviava a ogni chiusura e a ogni avvio. Dal 6/11 alcune installazioni restavano così a una versione vecchia.
  Ora quei processi non contano. Se la tua installazione è ferma, lancia `/aggiorna` una volta: dopo,
  l'aggiornamento automatico torna a funzionare da solo.
- L'aggiornamento automatico funziona anche con Python 3.8 e 3.9, come promette il README: prima, con il
  Python di sistema di un Mac, l'applicazione si fermava con un errore.
- La testata di Arturo e `/versione` dicono di chi è Arturo: Federico Nejrotti, con il link a
  stellakamikaze.org. Lo dicono anche il README, la licenza e i dati del plugin.
- Se il tuo `~/.claude` è un repository tuo con Arturo come upstream, e lo usi su un computer solo, ora puoi
  passare al plugin: `arturo migra --prova --unica-macchina` mostra cosa cambia, `arturo migra --unica-macchina`
  lo fa. Il tuo repository resta, e i file di Arturo escono con un commit. `arturo migra indietro` lo annulla
  (proposta n. 62).

**Il principio**: un aggiornamento che si rinvia per sempre è un aggiornamento che non c'è. Il segnale era nella
telemetria: solo "rinviato", mai più "applicato".

## 2026-11-09 — Gli aggiornamenti del plugin si fermano prima, e il gate dice il vero

**Cosa cambia**: correzioni alla catena dei rilasci e ai controlli che la provano.
- `/aggiorna` col plugin rifiuta un rilascio firmato vecchio pubblicato sotto un nome nuovo: la firma copre
  il nome scritto dentro il tag, e i due nomi devono coincidere. Prima si poteva riportarti indietro a una
  versione con una firma valida.
- Un tag senza firma (un tag "leggero") dice "possibile compromissione". Prima diceva "Non è un problema di
  sicurezza: aggiorna git e OpenSSH".
- Il MANIFEST firmato si controlla prima di installare, sui file del rilascio scaricato. Se il controllo
  dopo l'installazione fallisce lo stesso, Arturo rimette la versione di prima quando la sua cartella c'è
  ancora, e lo dice.
- `/setup` installa versioni fissate di Scrapling, markdownify e Impeccable: un rilascio nuovo di quei
  progetti non arriva più da solo con un'installazione.
- Per chi mantiene Arturo: il pacchetto firmato del plugin nasce dal tag del rilascio, non dall'albero di
  lavoro, e la verifica del pacchetto da pubblicare vuole la firma. La procedura di rilascio mette firma,
  verifica e push in un blocco solo, anche per il tag del plugin, e la prova di aggiornamento parte
  dall'ultimo tag di `origin/main`. `humanizer-origine.py` scrive lo sha intero.
- Il gate stampa `PASS` solo se è verde, conta i banchi di Python 3.8 (`py38=`) e, per un rilascio, si
  ferma se Python 3.8 manca. Confronta i suoi elenchi coi file di `tests/`: un banco nuovo non elencato, o un
  veleno mai lanciato, è rosso. I banchi delle guardie all'avvio danno rosso un banco che manca, invece di
  saltarlo. `gate-run.sh` esce 3 se il veleno cancella un file.

**Il principio**: una firma vale per quello che copre. Se il nome, i file o l'albero da cui nasce il
pacchetto restano fuori dalla firma, la firma è vera e il rilascio no.

**Da sapere**: Hallmark si installa ancora dalla testa del suo repository. Lo strumento `skills` non accetta un
commit fissato.

## 2026-11-09 — Le pulizie e le promesse sui tuoi dati dicono il vero

**Cosa cambia**: dieci correzioni a quello che Arturo toglie dai testi e a quello che promette.
- `/segnala` toglie anche gli indirizzi senza `https://` (`www.…`, `intranet.cliente.it/…`), quelli `ftp`
  e `ssh`, i nomi di immagini, audio, video, archivi e testi, la cartella personale nella forma di Git Bash
  e di WSL (`/c/Users/…`), e un nome di documento con le maiuscole e gli spazi ("Contratto Rossi Bianchi
  2026.pdf"). Restano i file di Arturo, come `CLAUDE.md` o `commands/fine.md`. Se prima di un nome c'è una
  parola minuscola che può esserne parte, l'anteprima lo dice con la riga "Da controllare".
- `arturo segnala invia` manda solo il file di `prepara`, uguale a quello dell'anteprima: un file scritto a
  mano o cambiato dopo non parte, e si rilancia `prepara`.
- Il ritratto di `/setup` toglie anche `pw`, `passphrase`, la chiave del wifi, il `cvv`, il numero dopo `pin`
  anche con una parola in mezzo ("Pin bancomat …") e l'IBAN scritto in minuscolo.
- Su Windows l'avvio non propone più il passaggio al plugin: lì non è ancora provato.
- Test, commenti ed esempi non hanno più nomi di persone né id veri di installazioni. Il controllo di
  igiene del repository li cerca, e la regola vale anche per questo file.
- Il README dice com'è davvero l'aggiornamento automatico: con un'altra sessione aperta il rilascio si
  installa alla chiusura dopo o all'apertura, e in un conflitto vince il file del rilascio, con la tua
  versione in `personale/conflitti/`; restano a te solo `settings.json` e i `CLAUDE.md`.
- `docs/privacy.md` dice che le email con una cosa da fare creano un task nell'elenco di chi mantiene
  Arturo, come cancellare gli eventi di Lancillotto e una segnalazione partita senza id.
- Il capitolo sui rail dice che un banco delle guardie rosso non ti interrompe: lo legge `/diagnosi`.
- Il README conta 31 guardie e automazioni e 7 strumenti in `hooks/`, e `arturo correzione` sta fra i
  comandi della CLI, non fra le skill.

**Il principio**: una promessa sui dati che il codice non mantiene è peggio di nessuna promessa, perché la
persona decide fidandosi. Dove il codice poteva mantenerla, ora la mantiene; dove no, il testo dice il vero.

**A chi serve**: a chi manda segnalazioni o fa il ritratto di `/setup` con documenti di lavoro, e a chi
decide se tenere gli aggiornamenti automatici leggendo gli Impegni.

## 2026-11-09 — /fine, /inizio e i comandi di Arturo non sbagliano più in silenzio

**Cosa cambia**: undici correzioni ai comandi di Arturo.
- `/fine` con un remote privato non salva più nella config i file `.env`, le chiavi, `credentials.json`,
  la cartella `secrets/`, `.venv`, `node_modules` e `__pycache__` di `personale/`. La riga di esito dice
  quali file ha lasciato fuori.
- Due computer che chiudono `/fine` uno dopo l'altro non si fermano più su `INDEX.md` con un rebase a metà:
  l'indice si ricostruisce dagli handoff e il salvataggio continua.
- Due `/fine` nello stesso momento non possono più creare il commit della memoria vuoto.
- Una riga di soli `=======`, come la sottolineatura di un titolo, non ferma più `/fine`. Un conflitto vero
  lo ferma ancora, e il messaggio dice in quale file.
- `/inizio --tutti` non annulla più un rebase o un merge già a metà in un progetto: lo lascia com'è e lo dice.
- `/inizio libro togli il flag --force` carica il progetto col compito, invece di rispondere "nome non valido".
- Il tasto o di `/dafare` dice "Aperta" solo se il terminale si apre davvero. Se il Mac nega il permesso,
  dice perché e mette il comando negli appunti.
- Una scadenza scritta senza anno vale la data più vicina: il 7 novembre "15/1" è il gennaio che viene, non
  quello passato. La conferma dice la data.
- Il controllo di un progetto Python senza test dice "nessun test", non più "rosso".
- Una riga sbagliata da un ponte di `/monitor` si scarta da sola, e le altre righe arrivano.
- Un documento Word rovinato non ferma più la lettura dei documenti di `/setup`.

**Il principio**: un comando che dice "fatto" senza averlo fatto, o "errore" senza un errore, insegna a non
leggerlo. Ognuno di questi casi ora ha una prova che cade sulla versione di prima.

**A chi serve**: a tutti. Le due correzioni di `/fine` sul salvataggio servono a chi tiene la config su un
remote privato da più computer.

---

## 2026-11-09 — Rotazione, segreti e controlli automatici più affidabili

**Cosa cambia**: venti correzioni ai controlli che girano da soli e al mod di Arturo.
- La rotazione della sessione la decide solo la sessione principale. Un agente al lavoro non riceve più
  l'avviso del contesto pieno e non può far ripartire la sessione a metà del lavoro.
- Se `/clear` non chiude la sessione, la rotazione si annulla e lo dice. Un `/clear` scritto ore dopo non
  riparte più da solo sul compito vecchio, e il secondo tentativo si ferma se stai scrivendo.
- I segreti dentro un JSON (`"password": "…"`, `"token": "…"`), le stringhe di Redis senza utente, le chiavi
  PGP o cifrate e le intestazioni `Authorization: Bearer` vengono redatti prima che Claude li legga. La sigla
  lascia leggibile il nome della chiave, e lo stesso valore dà sempre la stessa sigla.
- Il controllo dei tipi dopo una modifica non scrive più file `.js` accanto ai sorgenti.
- Con la memoria accesa, una nota non perde più la riga dopo un `updated:` vuoto né il rientro del corpo.
  Claude sa dove è finita una nota spostata e quando il frontmatter è rotto. Un testo incollato lungo non
  fa più scadere il richiamo.
- I simboli come ⌊ ★ ❯ nel codice non contano più come emoji.
- Un'email letta con `gws` che cita "invalid_grant" non ferma più il lavoro come se mancasse il login.
- Su Windows la barra non apre più finestre di terminale una volta all'ora. Un `git status` appeso non si
  moltiplica.
- Con una fonte esterna dei task, `/dafare` legge il JSON dell'esempio di `docs/fonte-task.md`, e la pagina
  `arturo web` dice che non la legge invece di mostrare un tavolo vuoto.

**Il principio**: un controllo automatico che sbaglia in silenzio è peggio di nessun controllo. Ognuno di
questi casi ora ha una prova che cade sulla versione di prima.

**A chi serve**: a tutti. Alla rotazione e alla redazione dei segreti in particolare a chi usa il mod di Arturo.

---

## 2026-11-09 — Col plugin, comandi e controlli trovano Arturo dove sta davvero

**Cosa cambia**: quattordici correzioni per chi usa Arturo come plugin. Col plugin il codice sta nella
cartella dei plugin di Claude Code, e `~/.claude` resta tua: diversi comandi lo cercavano ancora lì.
- `/system-audit` non dà più cinque errori falsi su un'installazione sana, e `/setup` arriva alla fine.
- `/fine --rotazione` torna a partire da solo a ogni compito chiuso. Lo stesso vale per `/segnala` alla fine
  della sessione e per `/diagnosi` quando `/inizio` la chiede.
- `/diagnosi`, `/inizio` e i todo riconoscono il mod di Arturo anche col plugin: prima lo davano per spento.
- `/inizio` non segnala più "controllo aggiornamenti non riuscito (rete?)" a ogni avvio. `/novita` dice se c'è
  un rilascio nuovo leggendo il catalogo firmato.
- `/setup` trova le sue guide (ritratto, intervista, Impeccable, Hallmark), salta la sincronizzazione tra
  macchine, che col plugin non c'è, e scrive lo stile come `arturo:Conciso`.
- L'identità di Git che scegli in `/setup` vale anche nei tuoi progetti: prima i loro commit restavano senza
  nome, o col nome del computer.
- Il tuo stile personale e il programma di `scrape` restano fra i tuoi file: un aggiornamento non li cancella.
- `/creaskill` dice occupato anche il nome di una skill di Arturo, come `fine`.
- La barra mostra di nuovo il task in corso, e il blocco sotto l'intestazione dice la versione di Arturo.
- La pagina dei todo, se si spegne, ti dà il comando giusto per riaprirla.
- Lancillotto si installa anche senza `gh`: il suo repository è pubblico e basta `git`.
- Metodo e stile Conciso dicono la stessa cosa quando un permesso ferma un passo.

**Il principio**: il codice si trova dalla sua cartella, i tuoi dati stanno in `~/.claude`. Un comando non
indovina dove sta l'altro.

**A chi serve**: a chi usa Arturo come plugin, e a chi sta per passarci con `arturo migra`.

---

## 2026-11-08 — Aggiornamenti e migrazione: niente più lavoro perso o blocchi senza motivo

**Cosa cambia**: otto correzioni a come Arturo si aggiorna e a come passa dal clone al plugin.
- `arturo migra indietro` non butta più quello che hai scritto dopo la migrazione: righe nuove in
  `personale/`, un'impostazione cambiata, un altro plugin installato. Prima di rimettere il clone com'era, li
  copia in `sostituiti-<data>/` dentro la copia di sicurezza, e te lo dice.
- Una copia di sicurezza rimasta a metà (disco pieno) non resta più accanto a `~/.claude`, e `migra indietro`
  non la prende per buona: prima metteva un `.git` incompleto al posto di quello vero.
- Il rapporto di `migra --prova` non dice più "il CLAUDE.md ripete 2 regole" a chi non ne ripete nessuna.
- Col plugin, `/aggiorna` porta anche le voci nuove di `settings.json` che il plugin non sa portare da solo:
  permessi, regole di blocco, `env`. Una voce cambiata anche da te si decide con `/setup`.
- Una copia di prova con un conflitto già risolto, che aspetta solo il tuo sì, non si scarta più alla chiusura
  di una sessione: resta finché non la concludi con `/aggiorna`.
- Un tuo hook mai salvato con un commit non blocca più ogni aggiornamento con "hook mancante". Una tua skill
  non salvata con lo stesso nome di una nuova di Arturo non lo blocca più: va in `personale/conflitti`, come un
  conflitto, e l'avvio te lo dice.
- Un `/clear` non installa più un aggiornamento con la sessione ancora aperta. L'installazione aspetta la
  chiusura vera.
- Se un aggiornamento sposta in `personale/` le righe che avevi aggiunto a un hook di sessione, l'avvio dopo te
  lo dice: sono commentate, e finché non le rileggi non girano.

**Il principio**: un aggiornamento automatico non deve mai costarti lavoro, né fermarsi per un motivo falso.

**A chi serve**: a chi ha già migrato al plugin o sta per farlo, e a chi risolve i conflitti con `/aggiorna`.

---

## 2026-11-08 — Telemetria: meno nomi in giro, tetti contro gli invii finti

**Cosa cambia**: undici correzioni al server della telemetria e alla parte di Arturo che gli parla.
- Su una seconda macchina, dove `~/.claude` è il clone del tuo repository privato senza `upstream`, i tuoi file
  non sembrano più file di Arturo: nella telemetria contano come `file:altro`. Prima il nome di un tuo documento
  modificato e non ancora mandato al tuo repository poteva uscire. Il messaggio dell'avvio sulla deriva resta.
- Il server tiene i nomi dei file di Arturo solo per le cartelle dove crei cose tue (anche `hooks/`); delle altre
  tiene la sola cartella.
- Il server non conosce più i nomi delle persone: le email a chi mantiene Arturo dicono le prime 8 cifre dell'id,
  come promette `docs/privacy.md`. La pagina della privacy ora dice anche cosa porta il recap di ogni mattina.
- Due sessioni aperte nello stesso momento non mandano più gli stessi eventi due volte, e non perdono quelli
  registrati durante l'invio. Una segnalazione in attesa parte una volta sola.
- Lo sportello delle segnalazioni chiede prima le più nuove e si ferma quando il server dice "troppe richieste":
  con più di dieci segnalazioni aperte, le risposte alle ultime arrivano.
- La pulizia di `/segnala` toglie le cartelle personali anche nei percorsi Windows con le barre doppie e con lo
  spazio nel nome (`C:\Users\Mario Rossi\...`).
- Sul server: tetti contro chi manda eventi finti con id inventati, un ritiro di segnalazione ripetuto che non
  suona più, il recap che dice quali eventi conta.

**Il principio**: la telemetria promette di non dire chi sei né cosa hai sul computer. Ogni nome che esce va
contro quella promessa, anche per sbaglio.

**A chi serve**: a chi usa Arturo su più macchine, a chi segnala da Windows, a chi lo mantiene.

---

## 2026-11-08 — Guardie più attente: commenti, push forzati, segreti nei commit, Windows

**Cosa cambia**: undici correzioni alle guardie che controllano i comandi prima che partano.
- Un commento in fondo a una riga (`ls # elenco`) non nasconde più il comando della riga dopo. Prima
  un `rm -rf` scritto lì passava senza domanda.
- `git push origin main --force` chiede conferma, come le altre forme che riscrivono o cancellano rami
  sul remoto (`-f`, `--force-with-lease`, `--mirror`, `--delete`, `:ramo`, `+ramo`), anche col flag in fondo.
- Il controllo dei segreti nei commit guarda anche i file nominati nel commit (`git commit -m x a.py`),
  i file aggiunti con `git add -f`, le chiavi OpenAI, e chiede conferma oltre i 200 file nuovi invece di
  fermarsi in silenzio ai primi 200.
- Uno script scaricato e passato a una shell si blocca anche con `;`, `&&` o una parentesi attaccata,
  con un `tee` in mezzo o con `sudo -E`. Il contrario: scaricare un file e poi leggerne un altro con
  `head f | python3 script.py` non si blocca più, e cercare con grep un testo come "bw export" nemmeno.
- `bash -lc`, `timeout 30`, `xargs sh -c` e `trap` non nascondono più un `rm -rf` o la lettura di `.env`.
- Le chiavi e le credenziali non si leggono senza conferma con `sort`, `uniq`, `jq` o `git diff --no-index`,
  né copiando o archiviando la cartella intera (`cp -R ~/.ssh`, `tar`, `zip`, `scp`). Anche il tool di
  ricerca Grep dentro `~/.ssh` chiede.
- Un invio di posta dopo un `&`, o con AppleScript su più righe, chiede conferma come gli altri.
- Su Windows `rd /s`, `del /s` e `Remove-Item -Recurse` su una cartella chiedono come `rm -r`.
- `git worktree remove --force` con file non salvati chiede davvero: la regola c'era, ma non partiva.
- Cancellare o riscrivere `settings.json` con `rm`, `command cp` o `perl -pi`, e toccare la chiave che
  verifica gli aggiornamenti, chiede conferma. Su Mac e Windows vale anche scritto con le maiuscole.

**Perché**: sono gli undici problemi delle guardie trovati dalla revisione completa del 7/11. Ognuno è
riprodotto in una cartella di prova prima della correzione, e il banco nuovo lo riprova a ogni rilascio.

**Da sapere**: niente cambia nel lavoro normale. Le domande nuove arrivano solo sulle forme che prima
passavano per sbaglio.

## 2026-11-08 — Aggiornamenti più sicuri: lo spazio nel nome utente, il catalogo del plugin, il ritorno indietro

**Cosa cambia**: quattro correzioni nella procedura che installa gli aggiornamenti.
- Con uno spazio nel nome della cartella utente (per esempio "Mario Rossi" su Windows), una copia di
  prova rimasta in attesa per un conflitto poteva far cancellare, al giro dopo, la cartella sopra la tua.
  Ora il registro della copia si legge per intero, e si cancella solo dentro la cartella delle copie di prova.
- Col plugin, un catalogo manomesso poteva far eseguire un comando prima del controllo della firma, o
  aggiungere ad Arturo componenti non firmati. Ora un indirizzo strano non arriva mai a git come
  opzione, e una voce del catalogo con chiavi in più vale "possibile compromissione".
- `/aggiorna indietro` ora dura: il rilascio tolto non si reinstalla da solo alla chiusura dopo. Lo
  rimette `/aggiorna`, oppure arriva un rilascio più nuovo.
- Quando concludi un conflitto rimasto a te, le tue versioni dei file già risolti col rilascio vanno in
  `personale/conflitti`, come negli altri aggiornamenti. Prima si perdevano in silenzio.

**Perché**: sono i due problemi critici e due dei problemi alti trovati dalla revisione completa del 7/11.
Il primo cancellava file veri: la prova l'ha riprodotto in una cartella di prova.

**Da sapere**: chi è già tornato indietro con una versione di prima ha ancora il comportamento vecchio
fino al prossimo aggiornamento.

## 2026-11-08 — Il promemoria del brief pesa la metà, e gli stop non passano dal brief

**Cosa cambia**: la riga che a ogni tuo messaggio ricorda a Claude prompt e brief scende da circa 900
a circa 470 byte. Dice le stesse regole: brief su ogni lavoro, anche piccolo, skill caricata una volta
per sessione, correzione a lavoro iniziato in una riga. Uno "stop" o un comando di controllo ora è
esente come una domanda: si esegue subito, senza brief.

**Perché**: il promemoria entra a ogni messaggio, anche a un "sì". In una sessione lunga pesava quanto
il corpo intero della skill, e ne ripeteva pezzi. La riga sugli stop dava ragione alla skill, che già
li esentava.

**Da sapere**: la riga che chiede `arturo correzione aggiungi` esce solo dove quel comando esiste.

## 2026-11-08 — La rotazione automatica non si ferma più per un testo rimasto nella casella

**Cosa cambia**: a fine compito la sessione si rinnova da sola (/clear, poi /inizio sul passo dopo). Prima,
se nella casella del messaggio c'era del testo, la rotazione si annullava subito. Ora aspetta. Se svuoti
la casella, parte. Se il testo resta fermo per un minuto, è un avanzo: la rotazione parte e il testo torna
nella casella della sessione nuova. Se mandi un messaggio, o continui a scrivere per dieci minuti, la
rotazione si annulla e rispondo a te.

**Perché**: il 7 e l'8/11 un "2" rimasto nella casella per ore ha annullato due rotazioni di fila. Il
registro `~/.claude/cache/rotazione-ultimo.txt` diceva "stai scrivendo: rotazione annullata", e la
persona doveva scrivere /clear e /inizio a mano.

**Da sapere**: il testo che stai scrivendo davvero non si perde. Una bozza che cambia tiene ferma la
rotazione, e una bozza vecchia torna nella casella dopo il rinnovo.

---

## 2026-11-07 — /novita riassume un arretrato grande, /setup controlla il permesso di GitHub prima del primo invio

**Cosa cambia**: se hai più di 10 novità da leggere, `/novita` non le racconta più una per una. Ti propone
un riassunto per temi, con in testa le correzioni delle tue segnalazioni, e approfondisci solo i temi che
scegli. `/segnala stato` riconosce anche le novità che citano una proposta col suo numero, quindi accanto
a una proposta realizzata non compare più "la correzione non è ancora uscita". Quando `/setup` crea il
repository privato che tiene allineati i tuoi computer, controlla prima il permesso `workflow` di GitHub e,
se manca, ti dà il comando per aggiungerlo: è un login nel browser, e lo fai tu.

**Perché**: la segnalazione n. 59 raccontava due problemi. Con 113 novità arretrate il racconto una per una
richiedeva ore, e le proposte n. 52, 53 e 54 risultavano ferme anche se erano già uscite. Con la
segnalazione n. 60 è arrivato il terzo: Arturo contiene un file di automazione, quindi senza il permesso
`workflow` GitHub rifiutava il primo invio e il repository restava vuoto.

**Da sapere**: nel repository privato puoi lasciare accese le Actions, le automazioni di GitHub. Quella di
Arturo gira solo nel repository pubblico: nel tuo viene saltata, quindi non consuma i minuti che GitHub
conta per le automazioni.

---

## 2026-11-06 — Col plugin vedi quando esce un rilascio nuovo

**Cosa cambia**: se usi Arturo come plugin, al massimo una volta all'ora Arturo controlla il catalogo dei
rilasci, senza installare niente. Il controllo parte all'avvio e dalla barra in basso, quindi funziona anche
con una barra tua. Se c'è una versione più nuova, la barra di Arturo mostra
`↑ Arturo <versione> · serve /aggiorna`, e la sessione dopo te lo dice anche all'avvio. L'avviso parte
anche quando `~/.claude` non è un repository git, come succede di solito dopo `arturo migra`. Il rilascio
lo installa `/aggiorna`, dopo averne verificato la firma. Col plugin l'avvio conta anche le novità da
leggere: prima non le vedeva, perché `NOVITA.md` sta accanto al codice.

**Perché**: col clone l'aggiornamento arriva da solo alla chiusura della sessione. Col plugin invece
l'aggiornamento parte solo quando scrivi `/aggiorna`, quindi la tua copia poteva restare indietro senza
che tu lo sapessi.

**Da sapere**: chi installa Arturo da zero non trova più novità vecchie da leggere. Finora il primo avvio
segnava come da leggere tutte le voci di questo file, più di cento, e l'avviso restava per molte sessioni.

## 2026-11-06 — Tre comandi per chi passa al plugin

**Cosa cambia**: dopo `arturo migra` restano tre cose da mettere in ordine, e ognuna ha ora il suo
comando.

- `arturo personale regole-doppie` elenca le regole consigliate da `/setup` che il tuo `CLAUDE.md`
  ripete, ora che col plugin le stesse regole arrivano all'avvio. Con `--togli` le toglie e tiene la
  copia di prima in `CLAUDE.md.prima-del-plugin`. Toglie solo le righe uguali alla regola: una riga che
  le somiglia, perché l'hai riscritta a modo tuo, resta e te la mostra.
- `arturo personale omonimi` elenca le tue skill, i tuoi comandi e i tuoi stili che hanno lo stesso nome
  di uno di Arturo. Col plugin, se scrivi solo il nome, parte il tuo. Per quello di Arturo scrivi
  `arturo:<nome>`. Se vuoi che il tuo prenda il posto di quello di Arturo, scrivi il nome in
  `personale/sostituzioni.txt`. Anche `/system-audit` segnala gli omonimi che non hai scritto lì.
- `arturo impostazioni adotta` serve a chi ha un `settings.json` fatto a mano: le voci di oggi restano
  come le hai scritte, e da lì in poi `arturo impostazioni applica` porta solo i cambi di Arturo. Se
  mancano regole di blocco di Arturo il comando si ferma e le conta, perché dopo non arriverebbero più.

**Perché**: col plugin, se scrivi solo il nome, parte la tua skill. Una skill nuova di Arturo con un nome
che usi già quindi non si vedrebbe mai, e `omonimi` te la fa trovare. Con `adotta` le differenze fra il
tuo `settings.json` e le impostazioni di Arturo smettono di contare come conflitti.

**Da sapere**: se personalizzi le guardie, in `protect_claude_md.local` c'è la categoria nuova
`dot-claude-progetto`, per la cartella `.claude` di un progetto: non vale per `~/.claude`, e la guardia ferma
comunque una modifica che romperebbe il JSON di un settings. Il README ora dice come decide una
guardia personale: con il codice di uscita 2 blocca il comando, con ogni altro codice diverso da 0 conta
come rotta e chiede conferma. E il `researcher` ora riporta anche l'estratto della fonte che regge ogni
risultato, così controlli a campione senza rifare la ricerca.

## 2026-11-05 — Arturo può uscire dalla tua cartella

**Cosa cambia**: c'è un comando nuovo, `arturo migra`, che porta Arturo dalla tua cartella
`~/.claude` al plugin di Claude Code. Prima si lancia `arturo migra --prova`: non cambia niente e
scrive un rapporto, con quello che succederebbe e quello che resta tuo. Le tue aggiunte ai comandi di
Arturo passano in `~/.claude/personale/`, i tuoi hook e i tuoi permessi restano, e tutto quello che
cambia ha prima una copia di sicurezza. `arturo migra indietro` rimette tutto com'era. Finché non
migri, Claude te lo ricorda all'inizio della sessione, una volta al giorno.

**Perché**: col plugin un aggiornamento cambia solo Arturo e non tocca mai i tuoi file. Oggi invece
Arturo e i tuoi file stanno nella stessa cartella, e una tua modifica può andare in conflitto con
l'aggiornamento. La migrazione la facciamo insieme: se usi Arturo, ti scrive Federico.

## 2026-11-05 — Le tue preferenze hanno una cartella sola

**Cosa cambia**: i file `.local`, quelli dove scrivi le tue scelte (i tuoi server in
`hosts-interni.local`, le API fidate, le tue guardie, come sono fatti i tuoi handoff, la fonte dei
task), adesso stanno tutti in `~/.claude/arturo/`. Non devi spostare niente: un file scritto prima in
`~/.claude/hooks/` o in `~/.claude/bin/` vale ancora, finché lo stesso file non c'è nella cartella
nuova. Se lo sposti, vale quello nuovo. I file in `~/.claude/arturo/` sono protetti come prima:
Claude non li cambia senza la tua conferma, perché un file `.local` può allentare una guardia.

**Perché**: è un passo per fare di Arturo un plugin di Claude Code. Col plugin il codice sta in una
cartella che Claude Code aggiorna da solo, e un tuo file accanto al codice si perderebbe. Le tue scelte
devono stare nella tua cartella, `~/.claude`, separate dal codice.

## 2026-11-04 — Le segnalazioni hanno una ricevuta e una risposta

**Cosa cambia**: quando mandi una segnalazione con `/segnala`, oltre al numero ricevi una ricevuta: un
codice che resta sul tuo computer. Con quello leggi la risposta di chi mantiene Arturo. Quando la
risposta arriva, l'avvio della sessione te lo dice, e `/segnala stato` la mostra. Se ti chiedono altre
informazioni, le aggiungi alla stessa segnalazione con `/segnala`, che le scrive con te. Puoi anche
ritirarla: dal server spariscono titolo, testo e aggiunte.

Nell'anteprima vedi due cose nuove. La prima è cosa Arturo ha tolto da solo dal testo: email, indirizzi
web, indirizzi IP, nomi dei computer di casa o dell'ufficio e nomi di documenti. La seconda è il pacchetto
tecnico, a caselle: versioni, esito dei controlli delle guardie e stato della config sono accesi; i file
di Arturo che hai cambiato, il messaggio d'errore intero e il legame coi tuoi dati d'uso sono spenti.
Accendi o spegni quello che vuoi. Il pacchetto si cancella dal server dopo 90 giorni.

**Perché**: una segnalazione partiva e poi non se ne sapeva più niente, finché una correzione non usciva
nelle novità. Chi mantiene Arturo non aveva un modo per chiedere un dettaglio mancante, e chi segnalava
non sapeva se era stata letta. Il legame coi dati d'uso adesso parte solo se lo scegli tu: prima partiva
sempre con la telemetria accesa.

## 2026-11-04 — Un lavoro iniziato fuori da un progetto si ritrova

**Cosa cambia**: se apri Claude fuori da un progetto e cominci un lavoro che continua nei giorni dopo,
`/fine` lascia un handoff breve col nome di quel lavoro, per esempio "preventivo-cucina". Dentro ci
sono dove eri arrivato, dove stanno i file e cosa resta da fare. Per riprendere scrivi
`/inizio preventivo-cucina`. Claude ti offre anche una cartella di progetto, e la crea solo se dici sì.

**Perché**: segnalazione n. 23. Il 15/10 aveva iniziato un lavoro fuori da un progetto, e il
26/10 non trovava più dove fosse: la sessione non aveva lasciato né file né handoff.

## 2026-11-04 — Claude dice prima dove non arriva

**Cosa cambia**: se chiedi un lavoro che Claude fa male anche impegnandosi, lo dice nel brief, prima
di provarci. Succede col disegno delle piste di un circuito stampato, col disegno a mano dentro
Illustrator, con una grafica da giudicare stampata o con un oggetto da costruire. La riga "Dove non
arrivo" dice due cose: la parte che resta a te e cosa fa Claude al suo posto. Per esempio la distinta
dei componenti, il budget, uno script che ricolora i file che salvi, il manuale che spiega ogni pista.
La stessa risposta arriva se chiedi solo "mi puoi aiutare con questo?".

**Perché**: al Computer Club una persona ha raccontato che sul mixer, arrivato alle schede, Claude non
lo aiutava più. Un tentativo scarso costa ore a chi lo deve buttare. Saperlo prima costa una riga, e
lascia il tempo per la parte in cui Claude serve davvero.

---

## 2026-11-04 — Una correzione detta una volta vale per tutta la sessione

**Cosa cambia**: quando correggi Claude, lui scrive la correzione in una riga (`arturo correzione
aggiungi`). Da lì la rilegge prima di ogni risposta, anche dopo una compattazione, e la passa ai
subagenti che lancia. `arturo correzione elenco` ti mostra cosa ha scritto, `arturo correzione togli N`
ne toglie una. Le correzioni restano sul tuo computer e valgono per la sessione: dopo `/clear` si
riparte da zero.

**Perché**: al Computer Club è capitato di vedere lo stesso errore tre volte di fila, ogni volta
dopo averlo fatto notare. Detta in chat, una correzione si allontana nel contesto, si perde nel
riassunto di una compattazione e non arriva ai subagenti. Una correzione che vale sempre, non solo
oggi, la metti nel `CLAUDE.md` con `/fine`.

---

## 2026-11-04 — Un aggiornamento rimandato non aspetta più le altre sessioni

**Cosa cambia**: se alla chiusura di una sessione l'aggiornamento automatico si ferma perché un'altra
sessione è ancora aperta, alla chiusura dopo si installa lo stesso, anche con altre sessioni aperte.
Prima aspettava che chiudessi l'ultima, oppure un'apertura di Claude Code con una sessione sola.

**Perché**: chi tiene sempre una sessione aperta restava indietro per giorni senza accorgersene. Le
sessioni rimaste aperte usano da subito i controlli nuovi, come dopo `/aggiorna`. Se una di loro dà
errori, chiudila e riaprila.

---

## 2026-11-04 — Reinstallare Arturo riporta tutto quello che è tuo

**Cosa cambia**: se reinstalli Arturo da capo col blocco del README o di `/setup`, tornano anche gli
handoff dei tuoi progetti, ogni tuo file `.local` (per esempio l'account Google scelto o le parole da
non cercare nella memoria) e le skill, i comandi e gli agenti che hai fatto tu, anche con `/creaskill`.
Un comando che Arturo ha tolto in un rilascio resta invece nella copia messa da parte.

**Perché**: la promessa era "non perdi niente di tuo", ma la lista dei file da riportare ne nominava
solo una parte. Ora un file è tuo se Arturo non l'ha mai avuto: non serve aggiornare una lista a ogni
file nuovo.

---

## 2026-11-04 — /inizio avvisa quando apri la terza sessione

**Cosa cambia**: se apri `/inizio` mentre altre due sessioni di Claude stanno già lavorando, su
qualunque progetto, la ripartenza apre con una riga: quante sono, quali, e a che punto è la finestra
di 5 ore. Il lavoro parte lo stesso: chiudere una sessione lo decidi tu. Le sessioni ferme su altri
computer o nel cloud non contano, e una sessione ripresa dalla rotazione automatica non avvisa.

**Perché**: proposta n. 54. Il limite delle 5 ore è uno solo per tutte le sessioni
dell'account. Dal 15/10 al 4/11 è scattato 9 volte, sempre con tre sessioni o più, e ogni volta ha
fermato più progetti insieme e lasciato agenti a metà. Con una sessione sola non è mai scattato.

---

## 2026-11-04 — /segnala guarda se la segnalazione è già partita

**Cosa cambia**: prima di mostrarti l'anteprima, `/segnala` guarda le segnalazioni già partite da questo
computer, anche da altre sessioni. Se una racconta lo stesso fatto, Claude te lo dice col numero e la
data, e ti chiede se mandare la nuova come aggiunta a quella. Decidi tu: niente blocchi. Un'aggiunta
porta solo il nuovo, per esempio un caso diverso o un messaggio esatto, e dice a quale segnalazione si
lega.

**Perché**: proposta n. 53. Su 21 segnalazioni partite dal 19/10 al 4/11, tre problemi sono
partiti tre volte ciascuno, da sessioni che non si vedevano fra loro. Il confronto lo fa Claude sul
fatto, non sulle parole: un conteggio di parole uguali legava due casi su tre di uno stesso problema.

---

## 2026-11-04 — /inizio ricorda i todo di Claude fermi da giorni

**Cosa cambia**: all'avvio, `/inizio` elenca i todo che Claude deve fare e che non hanno avuto un passo
da più di 3 giorni, con l'ID e i giorni. La riga c'è anche quando apri la sessione con un compito, e
nella rotazione automatica: dopo il compito Claude ne riprende uno, o ti chiede se toglierlo. Una nota
sul todo non azzera il conteggio: conta solo un passo vero (una modifica, un cambio di stato). Un todo
messo in fermo apposta, o che aspetta un altro todo, resta fuori. Se un todo fermo chiede le tue mani,
per esempio una prova a banco, Claude lo segnala come assegnato male e ti propone di passarlo a te.

**Perché**: proposta n. 52. Quattro decisioni passate a Claude il 28/10 erano ancora aperte il
4/11, dopo tre sessioni sullo stesso progetto: il compito nuovo passava sempre davanti.

---

## 2026-11-04 — Un agente ripreso fuori dalla sua copia si ferma e lo dice

**Cosa cambia**: un agente lanciato in una copia separata (`isolation: "worktree"`) che si ferma, per la
quota finita o la rete, e poi viene ripreso, adesso controlla dove si trova. Se la sua copia non c'è più
e lavora nella cartella della sessione che l'ha lanciato, riceve un avviso e non può modificare file né
lanciare comandi lì. Può leggere, si ferma e scrive nel report che la copia è sparita e cosa gli resta da
fare. La sessione decide: rilanciare il lavoro in un agente nuovo con la sua copia, oppure lasciarlo
lavorare lì.

**Perché**: segnalazione n. 51. Claude Code toglie la copia di un agente che si ferma senza
modifiche, e alla ripresa lo fa lavorare nella cartella della sessione, senza avviso. Due agenti su tre
hanno fatto commit sul ramo della sessione, e il file a metà di uno è poi andato perso (segnalazione n. 55).

---

## 2026-11-04 — L'avviso dell'aggiornamento dice cosa lo ferma

**Cosa cambia**: se hai modifiche non salvate con un commit in `~/.claude`, l'avvio non dice più che la
versione nuova "si installa da sola alla chiusura". Dice che è ferma, quali file la fermano, e come
sbloccarla: salvarle con `/fine`, e allora si installa alla chiusura dopo, oppure `/aggiorna` subito,
che le salva col tuo sì. La barra in basso dice "serve /aggiorna". Appena salvi le modifiche, l'avviso
torna a dire che si installa da sola. E quando un'installazione automatica non parte, l'avvio dice solo
questo, con i file che l'hanno fermata, senza ripetere nella riga dopo che si installa da sola.

**Perché**: segnalazione n. 49. L'aggiornamento automatico si fermava per una sua modifica non
salvata, ma l'avvio diceva insieme "si installa da sola alla chiusura" e "non è partito", e alla sessione
dopo tornava a promettere l'installazione senza dire come sbloccarla. Ha dovuto lanciare `/aggiorna` a
mano per scoprirlo.

---

## 2026-11-04 — Scrivere da terminale nei plugin installati chiede conferma

**Cosa cambia**: se Claude scrive da terminale dentro la cartella dei plugin installati
(`~/.claude/plugins`), ora ti chiede conferma, anche quando il file ha un nome qualsiasi e anche quando
il percorso è relativo, dopo un `cd ~/.claude`. Leggere quei file o copiarli altrove resta senza domande.

**Perché**: quando Arturo è installato come plugin, le sue guardie e il suo aggiornamento stanno in quella
cartella. Chi la modifica può spegnere le protezioni. La guardia lo sapeva già, ma il filtro che decide
quando chiamarla non conosceva quella cartella: passavano senza domande le scritture su file dai nomi
nuovi. Ora il filtro chiama la guardia anche su ogni comando che entra con `cd` in `~/.claude` o che parte
da lì, e lo stesso vale per una scrittura relativa nella cartella delle guardie.

---

## 2026-11-04 — Cancellare la cartella temporanea intera chiede conferma

**Cosa cambia**: un `rm -rf /tmp`, un `rm -rf "$TMPDIR"` o uno `shutil.rmtree` sulla cartella temporanea
del sistema ora ti chiedono conferma. Cancellare una cartella dentro, come una prova appena creata,
continua a passare senza domande.

**Perché**: la cartella temporanea intera contiene anche gli appunti di lavoro delle altre sessioni di
Claude aperte, e un comando che la svuota li cancella tutti. Le guardie la trattavano come una cartella
temporanea qualsiasi. Ora la guardia delle cancellazioni e l'elenco dei file di fine sessione usano la
stessa regola: la cartella temporanea stessa, o una che la contiene, non è mai un file temporaneo.

---

## 2026-11-04 — Claude salva a ogni compito finito

**Cosa cambia**: quando Claude finisce un compito che lascia una traccia (un commit, un file, una
decisione, un todo), salva subito con `/fine --rotazione`, anche se la sessione è ancora leggera:
scrive l'appunto della giornata, aggiorna i todo e la memoria, e ti dice cosa ha fatto e dove sta.
Se il passo dopo tocca ancora a lui, rinnova anche la sessione come prima. Se tocca a te, si ferma lì,
col lavoro già salvato.

**Perché**: prima il salvataggio andava insieme al rinnovo della sessione. Quando il passo dopo era tuo,
o non c'era, non partiva nessuno dei due, e i risultati restavano solo nella conversazione finché non
scrivevi `/fine`.

**Da sapere**: un'azione che non lascia niente da salvare, come accendere la musica, non fa partire il
salvataggio. E un aggiornamento di Arturo rimandato non si installa più quando la sessione si rinnova:
aspetta che tu riapra Claude Code. Prima poteva arrivare proprio in quel momento, e la sessione rinnovata
restava senza lo strumento che la fa ripartire da sola.

---

## 2026-11-04 — Da cosa è fatto Arturo

**Cosa cambia**: c'è una pagina nuova, `docs/come-e-fatto.md`, con il disegno di come stanno insieme
le parti. In cima ci sei tu, con la tua Orsa: le tue istruzioni, la tua voce e la tua memoria, che
gli aggiornamenti non toccano. Sotto c'è Arturo, che contiene skill adattate da progetti aperti di
altre persone e te ne consiglia altri. Più sotto ancora ci sono Claude Code e il modello di Anthropic.

```diagramma
  tu
   │  chiedi, correggi, scrivi come scrivi
   ▼
┌─ Orsa ─────────────── ~/.claude, è tua: gli aggiornamenti non la toccano ─┐
│  CLAUDE.md · personale/<skill>.md · memoria · todo · handoff              │
│  la tua voce: "Come scrivo" nel CLAUDE.md + personale/humanizer.md        │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ Arturo la legge e la rispetta
┌─ Arturo ─────────────── lo aggiorna chi lo mantiene, con rilasci firmati ─┐
│  guardie · comandi · skill · memoria Melchior · mod · telemetria          │
│                                                                           │
│  adattati da progetti aperti, dentro Arturo:                              │
│    humanizer ............. ◄── blader/humanizer (MIT)                     │
│    italiano-semplificato . ◄── ASD-STE100 via AminBlg/SimpleEnglish (MIT) │
│    prompt-master ......... ◄── nidhinjs/prompt-master (MIT)               │
│    intervista e deleghe .. ◄── mattpocock/skills (MIT)                    │
│                                                                           │
│  consigliati, li installi dalla loro fonte:                               │
│    Impeccable ............ ◄── pbakaus/impeccable (Apache-2.0)            │
│    Hallmark .............. ◄── Nutlope/hallmark (MIT)                     │
│    diagram-design ........ ◄── cathrynlavery/diagram-design (MIT)         │
│    scrape ................ ◄── D4Vinci/Scrapling (BSD-3)                  │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ hook, skill, comandi, permessi
┌─ Claude Code ──────────────────── di Anthropic, a pagamento ──────────────┐
│  il programma nel terminale: legge e scrive i file, lancia i comandi      │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ la conversazione esce dal tuo computer
                       il modello (Claude, sui server di Anthropic)
```

**Perché**: Arturo usa il lavoro di altri, e chi lo usa ha diritto di sapere di chi è ogni pezzo, con
quale licenza e chi lo aggiorna. La pagina ha anche la tabella di chi aggiorna cosa.

**Da sapere**: diagram-design, la skill per i diagrammi, è consigliata e si installa dalla sua fonte
(`docs/diagram-design.md`). La pagina dice anche come stanno insieme i tre lavori della scrittura:
`italiano-semplificato` per il testo tecnico, la tua voce per la prosa, `humanizer` per togliere i
segni dell'IA.

---

## 2026-11-04 — I testi che scrivi con Claude suonano tuoi

**Cosa cambia**: c'è una skill nuova, `humanizer`. Quando un post, un'email o una proposta suonano
scritti da un'IA, chiedi a Claude di renderli tuoi, oppure di passarli da `humanizer` prima di
consegnarli. La skill toglie i contrasti inventati ("non è solo X, è Y"), le chiuse a effetto, gli
elenchi di tre messi per abitudine, le lineette ovunque, le parole gonfie come "fondamentale" e
"ecosistema", e i resti della chat come "Spero ti sia utile". Non aggiunge fatti, nomi o numeri.

**Perché**: un testo che suona da IA si riconosce, e chi lo legge smette di fidarsi anche di ciò
che è vero. La skill segue il tuo modo di scrivere: se le dai un tuo testo come campione, imita
quello; altrimenti legge la sezione "Come scrivo" del tuo `CLAUDE.md`, che `/setup` ha scritto con
te. Il campione vince sulle regole: se tu usi le lineette, restano. La tua voce ha anche un file
tutto tuo, `~/.claude/personale/humanizer.md`, con i tuoi testi, le tue regole e le tue correzioni:
quando correggi un testo riscritto, Claude ti propone di aggiungere la correzione, e la scrive solo
col tuo sì. Per i testi in inglese la skill usa l'originale di blader così com'è.

**Da sapere**: è l'adattamento italiano di humanizer di blader, un progetto open source con licenza
MIT. Prende il posto del catalogo dei tic che stava dentro la skill `italiano-semplificato`, che
adesso usa lo stesso elenco: i cataloghi non sono più due.

---

## 2026-11-04 — Claude ti fa le domande giuste, e rispiega quando non è chiaro

**Cosa cambia**: quattro cose che succedono da sole, senza comandi nuovi.
Se chiedi un'idea ancora da decidere ("vorrei un sito per l'associazione"), Claude ti fa
domande a giri, ognuna con la sua risposta consigliata: puoi rispondere "sì a tutto".
`/guidami` cerca anche le cose che chiedi sempre uguali e te le propone da delegare, con la
scheda di come Claude le farebbe da solo. Quando un passo lo puoi fare solo tu su un sito, come
la console di Google Cloud, Claude ti prepara una procedura guidata da lanciare nel Terminale,
una schermata per volta. Se scrivi "non ho capito", Claude rispiega da capo in parole semplici,
invece di ripetere.

**Perché**: chi inizia non sa quali domande servono, e non sa cosa delegare. Davanti a dieci
passi scritti in chat, chi non ha mai usato un terminale perde il filo. Sono due dei blocchi che
Arturo vuole togliere: non sapere cosa chiedere, e il terminale.

**Da sapere**: le idee vengono da `mattpocock/skills` (licenza MIT), riscritte dentro
prompt-master, `/guidami`, la guida a Google e lo stile Conciso. La procedura guidata vuole un Terminale
vero: col prefisso `!` non può leggere quello che scrivi.

---

## 2026-11-04 — Se il controllo dei segreti non parte, Arturo ti dice perché

**Cosa cambia**: prima di ogni commit una guardia cerca password e chiavi nelle modifiche. Quando
non riesce a leggerle, adesso il popup dice il motivo e come ripararlo: la cartella appartiene a un
altro utente del computer, un altro git sta lavorando sullo stesso repository, l'indice di git è
rotto, oppure git ha impiegato più di 4 secondi. `/diagnosi` prova lo stesso controllo sul progetto
e riporta l'errore esatto.

**Perché**: la telemetria ha mostrato che in una settimana il popup "scansione fallita" è comparso
8 volte su un'installazione, e 7 volte la risposta è stata sì. Ogni sì faceva partire il commit
senza controllo dei segreti, e il messaggio non diceva cosa fare per rimetterlo in piedi.

**Da sapere**: il popup chiede ancora la conferma, e se dici sì il commit parte senza il controllo
dei segreti, come prima.

---

## 2026-11-04 — `/monitor` ti mostra le fonti che sa leggere

**Cosa cambia**: la prima volta che scrivi `/monitor`, Arturo ti dice quali fonti sa già leggere per
te (la posta, i todo, le sessioni con Claude, la memoria), quali mancano e cosa serve per
collegarle. Scegli tu quali usare, e Arturo salva la scelta in `data/monitor/fonti.json`.

**Perché**: lo smistamento, cioè il giro che legge quello che ti arriva e ne ricava le cose da fare
in ordine di urgenza, deve sapere prima quali fonti può leggere. Questo è il primo pezzo; il giro
quotidiano arriva con un prossimo aggiornamento.

**Da sapere**: come si aggiunge una fonte tua sta in `docs/monitor-ponti.md`.

---

## 2026-11-03 — Gli aggiornamenti non restano più fermi

**Cosa cambia**: se alla chiusura c'era un'altra sessione aperta, l'aggiornamento si installa
all'avvio dopo, quando quella che parte è l'unica sessione. Se una tua modifica a un file di
Arturo va in conflitto col rilascio, il rilascio si installa lo stesso. La tua versione resta in
`personale/conflitti/`, e all'avvio Claude ti propone di riportarla nella tua parte della config.

**Perché**: un'installazione è rimasta ferma per undici giorni. Alla chiusura c'era sempre un'altra
sessione aperta, e ogni aggiornamento veniva rinviato. Un conflitto, invece, fermava tutti gli
aggiornamenti dopo, finché non lanciavi `/aggiorna`.

**Da sapere**: un conflitto su `settings.json` o su un `CLAUDE.md` resta da risolvere con te, con
`/aggiorna`, perché quei file sono tuoi.

---

## 2026-11-03 — Quando modifichi le istruzioni di Arturo, ti chiede conferma una volta sola

**Cosa cambia**: quando Claude modifica un `CLAUDE.md`, ti compare una conferma sola. Prima la
guardia rifiutava la modifica e diceva a Claude di chiederti il permesso in chat. Poi un file di
sblocco faceva comparire un'altra conferma, e a volte una terza, se Claude provava dalla shell.

**Perché**: in una settimana le conferme sul `CLAUDE.md` sono state 47, e i sì 43. Una domanda che
ricevi due o tre volte per la stessa modifica insegna a dire sì senza leggere.

**Da sapere**: la protezione resta, perché ogni modifica a un `CLAUDE.md` chiede ancora. Se in
`hooks/protect_claude_md.local` hai scelto `allow` o `deny` per i `CLAUDE.md`, vale la tua scelta.

---

## 2026-11-03 — `/inizio` con una frase non ti chiede di ripeterlo

**Cosa cambia**: se scrivi `/inizio` seguito da una frase che è tutta compito, Arturo sceglie il
progetto e non aggiunge più "Se è un altro progetto, ripeti /inizio col nome giusto". L'invito resta
quando Arturo ha interpretato un nome scritto in modo diverso.

**Perché**: l'invito a ripetere serve quando un nome è stato letto male, non quando hai descritto il
lavoro da fare.

**A chi serve**: a chi apre le sessioni scrivendo il compito al posto del nome del progetto.

---

## 2026-11-03 — Un mod solo, con sei parti

**Cosa cambia**: i sei mod di Arturo diventano uno, `skills/arturo`, che Claude Code carica come
`arturo@skills-dir`. Le parti sono le stesse di prima e fanno le stesse cose: `apri`, `cache-fredda`,
`dafare`, `redazione-segreti`, `rotazione` e `testata`. Ognuna sta in una cartella di
`skills/arturo/hooks/`. Cambiano tre dettagli:
- per spegnere una parte la scrivi in `~/.claude/arturo/parti.json`, per esempio
  `{"spente": ["dafare"]}`, e vale dalla sessione dopo;
- il tool della rotazione si chiama `mcp__arturo__ruota`;
- la barra di `/dafare` riparte accesa, anche se l'avevi nascosta con `/dafare nascondi`.

**Perché**: meno pezzi da caricare e da tenere allineati. Lo stesso mod entra nel pacchetto plugin di
Arturo, dove il plugin lo porta con sé: il tool e i comandi hanno lo stesso nome nel clone e nel plugin.

**A chi serve**: a tutti. Vale dalla prossima sessione aperta dopo l'aggiornamento. Se avevi spento un
mod con `claude plugin disable`, quella scelta non vale più: scrivi la parte in `parti.json`.

---

## 2026-11-03 — Escono i mod `riscrivi-bash` e `gws`: al loro posto due hook

**Cosa cambia**: esce il mod `riscrivi-bash`, ed esce il mod `gws`. I comandi restano quelli che
scrive Claude: nessun mod li cambia più prima di eseguirli. Quello che facevano i due mod lo fanno
l'avvio e due hook:
- zsh si comporta come bash grazie all'avvio, come dalla 0.2.0. Un glob in un'opzione senza
  virgolette (`--include=*.md`) ora parte com'è, senza blocco.
- `timeout`, che sul Mac non esiste, non viene più tolto: `bash-dispatcher.sh` ferma il comando e
  dice a Claude come scriverlo.
- `gws gmail messages` non viene più corretto: `hooks/gws-esito.py` ferma il comando e dà a Claude
  la forma giusta, `gws gmail users messages`.
- Se `gws` fallisce per credenziali mancanti, lo stesso hook ti avvisa in una riga, dice a Claude di
  fermarsi e chiederti il login, e rifà subito il controllo dei token.

**Perché**: in modalità auto Claude Code respinge un comando cambiato da un mod dopo la sua
approvazione, e il comando va rilanciato identico. Un hook che ferma e spiega non cambia niente: il
comando che parte è quello approvato.

**A chi serve**: a tutti. Vale dalla prossima sessione aperta dopo l'aggiornamento. Se avevi spento
uno dei due mod con `claude plugin disable`, non devi fare niente.

---

## 2026-11-03 — All'avvio il blocco di Arturo, con la stella

**Cosa cambia**: sotto l'intestazione di Claude Code, al posto della riga della 0.2.0, compare un
blocco di tre righe accanto a una stella in pixel che pulsa per una ventina di secondi. La prima riga
dice "Arturo" e il numero della versione. La seconda dice lo stato in parole: le modifiche non ancora
rilasciate, un aggiornamento in arrivo, un controllo che non parte. La terza ha due link: la roadmap
e la pagina per mandare Arturo a qualcuno. Quando la roadmap cambia, o ogni due settimane, il link
della roadmap lo dice. In una finestra stretta la stella sparisce e restano le righe.

**Perché**: la riga della 0.2.0 usava sigle e numeri. Il blocco dice cosa fare in parole, e porta
alla roadmap chi vuole commentare cosa arriva.

**A chi serve**: a tutti. Si vede dalla prossima sessione aperta dopo l'aggiornamento. Per non vedere
più l'invito alla roadmap scrivi `{"pausa": "sempre"}` in `~/.claude/session-env/roadmap-vista.json`.

---

## 2026-11-03 — In modalità auto un comando parte al primo colpo

**Cosa cambia**: in modalità auto molti comandi venivano respinti una volta e andavano rilanciati
identici, circa 15 volte in un'ora di lavoro (segnalazione n. 45 e segnalazione n. 46). Succedeva
ai comandi con un `*`, un heredoc, un `=` o una variabile. Ora partono al primo colpo. In più
`/inizio` controlla che la copia separata, quando un'altra sessione lavora sullo stesso progetto,
parta dal tuo ultimo lavoro salvato e non dalla copia online.

**Perché**: il mod `riscrivi-bash` aggiungeva `setopt` davanti al comando dopo che la modalità auto
lo aveva già approvato, e Claude Code respinge un comando cambiato dopo l'approvazione. Adesso
quelle opzioni di zsh le imposta l'avvio della sessione una volta sola, e il comando resta com'è.

Dopo la 0.2.0, se l'avvio non ha scritto le opzioni (una sessione aperta prima dell'aggiornamento),
il mod mette ancora `setopt` davanti, ma una volta sola: il rilancio passa al secondo colpo e i
`setopt` non si accumulano più (segnalazione n. 47 e segnalazione n. 48).

**A chi serve**: a chi usa la modalità auto su un Mac, cioè quasi a tutti. Vale dalla prossima
sessione aperta dopo l'aggiornamento.

---

## 2026-11-03 — Arturo ha un numero di versione: questa è la 0.2.0

**Cosa cambia**: la versione di Arturo non è più una data ma un numero. Questo rilascio è la
0.2.0, e la testata all'avvio scrive "Arturo 0.2.0". I rilasci di prima hanno ricevuto un numero
anche loro, dalla 0.1.0 (12 ottobre) alla 0.1.29 (3 novembre mattina). L'ultima cifra sale a ogni
rilascio di correzioni, quella di mezzo quando esce un blocco della roadmap: il prossimo, il plugin,
sarà la 0.3.0. La 1.0 sarà il rilascio pubblico.

**Perché**: una data diceva quando era uscito un rilascio, non quanto Arturo era cresciuto. Con il
numero la roadmap può dire in quale versione arriva ogni cosa.

**A chi serve**: a tutti, senza fare niente. L'aggiornamento arriva come sempre alla chiusura della
sessione. Se segnali un problema, la versione da scrivere è il numero.

---

## 2026-11-03 — A ogni passo finito la sessione si rinnova da sola

**Cosa cambia**: quando Claude chiude un passo del piano o un compito, con i test verdi, salva con
`/fine --rotazione` e rinnova la sessione da solo: `/clear`, poi `/inizio` sul passo dopo. Tu non scrivi
più `/fine`, `/clear` e `/inizio` a mano fra un passo e l'altro. Il `/fine` completo gira una volta al
giorno, dalle 18. Le note che chiedono il tuo sì aspettano nell'handoff, e il prossimo `/fine` che scrivi
tu te le propone.

**Perché**: una sessione lunga si appesantisce e Claude ricorda peggio. Una sessione nuova a ogni passo
riparte leggera, con il contesto che serve.

**A chi serve**: a chi lavora su piani a più passi. La rotazione non parte se premi Esc, se c'è un
errore, se hai del testo nella casella o se la sessione dura meno di 3 minuti. Si spegne con
`ARTURO_ROTAZIONE=0`.

---

## 2026-11-03 — Arturo si presenta all'avvio, e i banchi rossi non ti disturbano più

**Cosa cambia**: all'avvio, subito sotto l'intestazione di Claude Code, compare una riga di Arturo:
la sua versione, quella di Claude Code, la deriva della tua config (quanti file di Arturo hai cambiato)
e l'aggiornamento in arrivo, se c'è. `/versione` la ripete col dettaglio. I banchi di prova delle
guardie, quando diventano rossi, non compaiono più sotto il prompt né all'avvio: ripartono da soli
dopo mezz'ora, e se restano rossi il nome del banco arriva a chi mantiene Arturo con la telemetria.

**Perché**: l'avviso dei banchi chiedeva a te di riparare una cosa che ripara chi mantiene Arturo, e
spesso era un rosso passeggero. La riga di testata dice invece in un colpo d'occhio con quale Arturo
stai lavorando. Il logo di Claude Code resta: nessuna opzione e nessun mod lo può sostituire.

**A chi serve**: a tutti. Se hai spento la telemetria, i banchi rossi restano sul tuo computer, in
`~/.claude/cache/banchi-ultimo-esito.txt`, e `/diagnosi` li legge.

---

## 2026-11-03 — /fine pesa meno, e a sessione vuota fa solo il sync

**Cosa cambia**: `/fine` è lungo poco più della metà. Le parti che servono solo in un caso (il
worktree, la retention, le tue aggiunte alla coda, gli opzionali) stanno in file di `shared/` che
Claude legge solo quando quel caso si presenta. Se la sessione non ha file, commit, todo né progetto,
`/fine` salta tutte le fasi e fa solo il sync della config.

**Perché**: proposta n. 29. `/fine` entrava intero nel contesto a ogni lancio, anche a sessione
vuota, e pesava sull'uso di Claude Code più di ogni altro comando.

**Da sapere**: le fasi e le regole sono le stesse. Il modello resta quello della sessione.

## 2026-11-03 — Con due Chrome collegati, Claude resta su quello che hai scelto

**Cosa cambia**: se hai più Chrome collegati a Claude, Claude ricorda il browser che hai scelto e,
dopo un errore di collegamento, controlla di essere ancora lì. Se è tornato sull'altro, lo
riseleziona e te lo dice. Per farti scegliere, descrive ogni browser da quello che mostra.

**Perché**: segnalazione n. 44. I nomi dei browser ("Browser 1", "Browser 2") cambiano durante la
sessione, e dopo una disconnessione i comandi tornavano sul Chrome sbagliato senza avviso. La causa
sta nell'estensione di Chrome: Arturo non può correggerla, ma può far controllare Claude.

## 2026-11-03 — Un amend non riscrive più il commit di un'altra sessione

**Cosa cambia**: `git commit --amend` chiede conferma se l'ultimo commit del repository non l'ha
fatto la stessa sessione. Se il commit è suo, tace come prima.

**Perché**: segnalazione n. 25. Due sessioni lavoravano sullo stesso progetto. Fra il commit di una e
il suo amend per un refuso, l'altra aveva fatto un commit, e l'amend ha riscritto quello. Nessuna
guardia l'aveva fermato.

**Da sapere**: per riconoscere i suoi commit, Arturo annota dopo ogni `git commit` l'ultimo commit
della sessione, in un file di `~/.claude/session-env`. Un amend su un commit di ieri chiede anche se
il commit è tuo: conferma. Per un refuso nel messaggio basta lasciarlo. `git reset` e `git rebase`
restano come prima.

## 2026-11-03 — La telemetria dice anche come usi Arturo, non solo quanto

**Cosa cambia**: alla chiusura di ogni sessione Arturo registra quanto è durata e quanti messaggi
hai scritto, solo in fasce larghe (meno di 5 minuti, fino a 30, fino a 2 ore, oltre; 1, da 2 a 5, da
6 a 20, oltre 20 messaggi), e quali skill di Arturo hai usato. Per contarli legge sul tuo computer la
cronologia della sessione: non ne esce nessun testo, e una skill tua conta come `altro`. Alla prima
sessione dopo l'aggiornamento Claude ti dice cosa esce di nuovo e come spegnerlo.

**Perché**: finora chi mantiene Arturo vedeva quante sessioni apri, non come lavori. Una sessione di
due minuti che finisce con `/fine` e una di due ore pesano uguale. Con le fasce si vede dove Arturo
ti fa perdere tempo, per esempio una chiusura lunga anche a sessione vuota.

**Da sapere**: la pagina [privacy](docs/privacy.md) ora dice la base giuridica senza riserve, il
legittimo interesse, e dice che l'email del lunedì a chi mantiene Arturo porta la sezione "Chi lo
usa". La telemetria si spegne sempre con `python3 ~/.claude/bin/arturo telemetria spegni`.

---

## 2026-11-02 — /inizio capisce una frase, e un passo fermato diventa un comando per te

**Cosa cambia**: se scrivi a `/inizio` cosa vuoi fare senza il nome del progetto ("oggi ho
scaricato molti documenti, riordinameli"), la frase diventa il compito della sessione. Claude ti
propone il progetto più vicino, o di lavorare dove sei, e non te la fa riscrivere (segnalazione
n. 39). Un testo molto lungo non dà più un errore tecnico con Python 3.9 (segnalazione n. 42).

Quando il controllo di sicurezza della modalità auto di Claude Code ferma un passo che hai già
approvato, non ti chiede niente: il passo resta fermo. Ora Claude ti prepara un solo comando da
lanciare tu col prefisso `!`, e ti dice in una frase cosa fa. Vale per la riga di Homebrew in
`~/.zprofile` (segnalazione n. 36), per lo sblocco di una guardia (segnalazione n. 38) e per un
passo su un tuo server (segnalazione n. 41). Lo sblocco delle guardie sui servizi di avvio e sui file
di config lo lanci sempre tu, col prefisso `!`.

**Da sapere**: se il progetto sta fuori dalle cartelle che Claude Code ha aperto, la shell torna alla
cartella di partenza dopo ogni comando. `/inizio` ora se ne accorge e ti propone `/add-dir`, e fino
ad allora `/inizio` e `/fine` lavorano nella cartella giusta (segnalazione n. 37). Se colleghi Chrome
con `/chrome` a sessione aperta, gli strumenti del browser arrivano solo dopo `/exit` e
`claude --continue`: Claude ora te lo dice subito (segnalazione n. 40). Un programma che macOS avvia
da solo (un LaunchAgent) non può scrivere in iCloud Drive, Documenti e Scrivania: Claude mette dati e
script altrove.

**Il principio dietro**: quando Claude non può fare un passo, ti dice subito il gesto che serve,
in una riga.

---

## 2026-11-01 — Arturo si installa incollando un link in Claude Code

**Cosa cambia**: per installare Arturo ora basta Claude Code. Scrivi `claude` e incolla la frase
`Installa Arturo: https://arturo.stellakamikaze.org/inizia/`. Claude legge la pagina, scarica lo
script, lo confronta con la copia su GitHub e lo lancia dopo il tuo sì. Se manca un programma, lo
installa col tuo sì. Lo script mette Arturo dentro `~/.claude` senza spostare la cartella: login,
conversazioni, plugin installati e il tuo `CLAUDE.md` restano dove sono. I file sostituiti, compreso il
`settings.json` che avevi, vanno in una copia con la data nel nome: `/setup` ti propone di riportare
hook, plugin e preferenze. Poi scrivi `/exit`, `claude` e `/setup`. `/setup` fa in silenzio i controlli
tecnici e ti fa conoscere da Claude: con un sì legge le tue ultime conversazioni, con un altro sì
guarda le cartelle che gli indichi, e ti propone un `CLAUDE.md` con la fonte di ogni riga. Alla fine
ti propone un primo lavoro vero, sul tuo materiale.

**Da sapere**: la lettura delle cartelle non apre mai cartelle di sistema, cartelle nascoste,
`.ssh`, chiavi, password manager, file `.env`, credenziali e documenti d'identità, di salute o di
banca. Da Download legge solo i nomi. Quello che legge passa dalla conversazione con Anthropic, come
ogni richiesta a Claude, e non va a chi mantiene Arturo. In telemetria esce solo che hai passato le
fasi 2b e 2c, mai il ritratto. Quello che legge resta nella cronologia della conversazione, che Claude Code
tiene sul computer e cancella da sola dopo 90 giorni: Arturo non ne fa altre copie. La strada a mano
resta, nel README e sul sito, per chi preferisce il terminale. Le finestre di sistema, come
l'installazione degli strumenti di Apple o la conferma di Windows, le confermi tu.

**Il principio dietro**: la persona fa solo quello che solo una persona può fare, e vede tutto quello
che Claude legge.

---

## 2026-11-01 — Le guardie del 31/10 chiudono i buchi trovati dalla revisione

**Cosa cambia**: il giorno dopo il cambio che ha tolto le conferme sul tuo lavoro, una revisione ha
cercato i modi per far passare un rischio vero senza conferma. Ne ha trovati 38, e una seconda
revisione, sulle correzioni, ne ha trovati altri 7: ora sono chiusi tutti e 45.
Qualche esempio. Uno stash conta come salvato solo se il comando salva proprio quello stash, e
`git stash clear` chiede. Un file caricato con `curl -d '@file'` chiede come `curl -d @file`. Un link
`mailto:` chiede anche se sta in una variabile. Un commit con un segreto chiede anche dopo un `cd -`.
Leggere una chiave privata in `~/.ssh` chiede, qualunque nome abbia. `rm -rf /*`, `rm -rf ~/*` e la
cancellazione del disco intero su Windows sono bloccati.

**Cosa resta uguale**: le conferme tolte il 31/10 sul tuo lavoro restano tolte. Un comando come
`find . | xargs grep -n rm` ora tace: prima chiedeva per la parola `rm` nel testo cercato.

**Il principio dietro**: togliere una conferma vale solo se il rischio vero resta coperto, e lo si
prova cercando apposta il modo di aggirarla.

---

## 2026-10-31 — Su Windows le guardie leggono il comando intero

**Cosa cambia**: se usi Arturo su Windows, le guardie leggono un comando su più righe come lo legge
bash. Prima un a capo scritto da `jq` o da python su Windows portava un carattere in più, e un
comando che continuava sulla riga dopo poteva mandare un file a un sito esterno senza chiederti
conferma. Ora la guardia lo vede e chiede. Su macOS e Linux non cambia niente.

**Da sapere**: chi mantiene Arturo prova ogni rilascio anche su Windows. Alcuni controlli lì non si
possono provare, perché Windows non concede i link simbolici senza la Modalità sviluppatore: il
controllo lo dice come salto, invece di passare in silenzio. Il rilascio si prova per intero su un Mac.

**Il principio dietro**: una guardia deve leggere il comando come lo esegue il sistema, non come appare.

---

## 2026-10-31 — Meno conferme sul tuo lavoro, le stesse guardie sui rischi veri

**Cosa cambia**: le guardie smettono di chiederti conferma per il lavoro tuo che si può rifare. Un
`rm` dentro una cartella temporanea, anche dopo un `cd`, non chiede più: la guardia segue i `cd` e
guarda la cartella vera. Cancellare un ramo git non chiede se i suoi commit stanno anche altrove.
Le guardie chiedono ancora per i rischi veri: un file che parte verso un sito esterno, un'email, un
link `mailto:` aperto da un programma, un segreto in un commit, la cancellazione di un ramo o di uno
stash che esistono solo lì. In modalità auto Arturo dice al classificatore di Claude Code quale
lavoro è tuo: le tue macchine, i tuoi repository, i deploy delle tue app, la lettura del web. Le
regole che negavano tutta una famiglia di comandi sono diventate più strette: per esempio leggere
`~/.ssh/config` si può, leggere una chiave no (dal 1/11 anche una chiave con un nome libero).

**Se una conferma ti sembra inutile**: chiedi a Claude da dove viene. Una conferma di una guardia si
allenta coi file `.local` in `hooks/`. Un diniego del classificatore si allarga con una riga in
`autoMode`, che Claude ti propone e scrive dopo il tuo sì. Il README lo spiega nella sezione
"Personalizzazione".

**Il principio dietro**: una guardia che chiede sempre insegna a dire sì senza leggere. Le conferme
servono solo dove un errore non si annulla.

---

## 2026-10-30 — Hallmark costruisce le pagine nuove, insieme a Impeccable

**Cosa cambia**: se fai siti o pagine, `/setup` nella fase 8c ti propone, dopo Impeccable, anche
Hallmark, una skill pubblica di Together AI. Hallmark costruisce da zero una pagina nuova, come una
landing o un sito vetrina: sceglie un tema da un catalogo di cinquanta, usa foto vere con il credito
e controlla la pagina su otto larghezze. Impeccable resta la guida: parte per prima, tiene le pagine
che esistono già, le app e le dashboard, scrive `DESIGN.md` e fa le rifiniture. Con tutte e due
installate, `/setup` ti propone una riga per il tuo `CLAUDE.md` che fa lavorare le due skill in
catena, e la scrive solo dopo il tuo sì. Come funziona e come si installa da sola:
`docs/hallmark.md`.

**Il principio dietro**: ogni skill fa la parte in cui è più forte, e il passaggio fra le due è
scritto. Arturo non copia nessuna delle due: le installi dagli autori e ricevi le loro versioni nuove.

---

## 2026-10-30 — /fine chiude in un comando, e i tuoi todo possono stare nel tuo strumento

**Cosa cambia**: la parte finale di `/fine` è un comando solo. Controlla l'handoff, mette nel cestino
gli handoff vecchi che ti ha mostrato prima e nessun altro, rigenera l'indice, poi salva e manda la
config. La memoria, il tuo CLAUDE.md, i todo e `personale/` partono solo verso un repository privato, e
mai i file di servizio della memoria. Prima un modo di `git add` su Windows poteva non salvare
`personale/` senza dirlo. Se tieni i todo in un altro strumento, un programma tuo indicato in
`bin/fonte-task.local` li legge e li scrive al posto dell'archivio di Arturo (`docs/fonte-task.md`).
Se quello strumento non risponde, `/inizio` mostra i task dell'ultimo handoff con l'avviso NON
VERIFICATO, invece di dire che non c'è niente. `/inizio` riconosce il progetto anche quando scrivi il
compito subito dopo il nome o un nome a metà, e dice come l'ha interpretato. Il compito non passa più
dalla shell: un `$(...)` scritto lì non viene eseguito. I passi tuoi di `/fine` stanno in
`personale/fine-coda.py`, e le tue regole sugli handoff, sui progetti contenitore e sui tuoi script in
tre file `hooks/*.local`: gli aggiornamenti non li toccano.

**Il principio dietro**: i passi che non chiedono giudizio girano in un processo solo, e i tuoi dati
partono solo dove hai detto tu.

---

## 2026-10-30 — Le tue guardie accanto a quelle di Arturo, e meno conferme a vuoto

**Cosa cambia**: puoi aggiungere guardie tue senza toccare quelle di Arturo, e senza perderle al
prossimo aggiornamento. Le nomini in `hooks/bash-dispatcher.local`, una per riga, con il punto in cui
devono girare: prima del controllo dei comandi pericolosi, al suo posto sui comandi che toccano
`~/.claude`, dopo una conferma per farla cadere, o in fondo. In `hooks/protect_claude_md.local` scegli
cosa fare quando Claude modifica CLAUDE.md, i settings o gli hook: chiedere, lasciar fare o bloccare.
Lo sblocco che dai per una modifica protetta vale per la tua sessione, e chiudere un'altra finestra
non lo toglie più. Se lavori su più computer, l'avvio vede di nuovo il lavoro arrivato dagli altri
anche quando Arturo è collegato come upstream, e ti avvisa se la config è ferma a metà di un rebase.
Il passaggio fra computer non spezza più un aggiornamento di Arturo appena installato.
Due conferme in meno: `curl … | python3 -m json.tool`, che formatta il JSON e non esegue niente, e i
comandi di rete che non caricano un file. La conferma resta sull'invio di un file dal tuo computer,
anche con un `&` dentro l'indirizzo.

**Il principio dietro**: le regole tue stanno in file tuoi, che Arturo legge come dati e non esegue.
I file che proteggono tutto il resto, fra cui i due `.local`, restano fuori dalla tua scelta.

---

## 2026-10-30 — /fine è un salvataggio, e la barra tiene il ramo anche nella config

**Cosa cambia**: quando la conversazione si avvicina al limite, Claude ti propone `/fine` per
salvare il lavoro, e dopo puoi continuare nella stessa sessione. `/clear` e `/inizio` per ripartire da
capo te li nomina una volta sola per sessione, non a ogni avviso. La barra in basso mostra il ramo
anche quando lavori sulla config (`~/.claude`), su un progetto con maiuscole o spazi nel nome, o in
una copia a parte aperta da `/inizio`: prima in quei casi il ramo spariva.

**Il principio dietro**: un avviso che ripete sempre la stessa proposta smette di essere letto.

---

## 2026-10-29 — La scheda del terminale dice il progetto vero, "LAVORANDO" mentre Claude lavora e "SBLOCCA" solo quando servi tu

**Cosa cambia**: il titolo della scheda è il nome del progetto. Mentre Claude lavora diventa
"LAVORANDO · <progetto>", anche a turno finito se aspetta un comando o un agente lanciato in
background. Quando Claude aspetta te diventa "SBLOCCA · <progetto>": per una richiesta di permesso, una
domanda, un errore, o dopo un minuto fermo. Prima bastava la fine del turno, e la scheda diceva "tocca
a te" anche mentre Claude aspettava il risultato di un gate. Un server lasciato acceso (vite, un server
locale di anteprima) non conta come lavoro: nessuno ne aspetta la fine. Il nome è quello che `/inizio` ha trovato:
"/inizio due mondi" mostra "due-mondi-myway", non "due". Senza `/inizio` vale la cartella del
progetto in cui Claude scrive i file.

**Il principio dietro**: la scheda serve a vedere da fuori quale sessione ti aspetta davvero. Un
avviso che scatta a vuoto insegna a ignorarlo.

**Nel Terminale di macOS**: accanto al nome compariva in grigio il processo ("caffeinate ◂ claude").
Alla prima sessione dopo l'aggiornamento Arturo crea il profilo "Arturo", una copia del tuo con colori
e font uguali, senza processo, cartella e indicatore di attività nel titolo, e lo mette su tutte le
schede. Te lo dice con una riga all'avvio. La campanella resta: una scheda in secondo piano che
aspetta te la mostra, insieme a "SBLOCCA". Per tornare al profilo di prima: `python3 ~/.claude/bin/arturo schede ripristina`.

---

## 2026-10-29 — Claude trova il comando arturo per nome, una correzione resta una riga, la barra dice il progetto

**Cosa cambia**: all'avvio della sessione Arturo mette `~/.claude/bin` fra i percorsi dei comandi di
Claude. Così `arturo todo` funziona anche senza `python3 ~/.claude/bin/` davanti, e Claude non perde
un giro a cercarlo (segnalazione n. 33). Il promemoria che arriva con ogni messaggio dice anche che una
correzione a lavoro iniziato è una riga, "Brief corretto: ...", come nella skill prompt-master: niente
prompt e brief riscritti da capo per un nome di cartella (segnalazione n. 34). La barra in basso mostra
il progetto aperto, lo stesso della scheda del terminale, anche se hai aperto Claude Code dalla home
(segnalazione n. 35).

**Il principio**: due regole che si contraddicono costano a ogni messaggio. Una sola fonte, detta uguale
dove la si ripete.

---

## 2026-10-29 — Un handoff tolto da /fine si recupera per un mese

**Cosa cambia**: quando `/fine` tiene solo gli ultimi cinque handoff di un progetto, quelli vecchi non
si cancellano più. Vanno in `~/.claude/data/handoffs/.cestino/`, nella cartella del progetto, e ci
restano 30 giorni. Per riaverne uno, chiedi a Claude di riportarlo indietro, oppure sposta tu il file
da `~/.claude/data/handoffs/.cestino/<progetto>/` a `~/.claude/data/handoffs/<progetto>/`. Dopo 30
giorni il cestino si svuota per tutti i progetti, anche per quelli che non chiudi più con `/fine`. Il
cestino resta sul tuo computer e non entra in git (segnalazione n. 26).

**Il principio**: un file della persona non sparisce senza una via per tornare indietro.

---

## 2026-10-29 — Un file con le lettere accentate non fa più chiedere conferma a ogni commit

**Cosa cambia**: se nel commit c'è un file salvato con una codifica vecchia, come il CSV di una banca,
la guardia dei segreti lo legge lo stesso. Prima non riusciva a leggere le lettere accentate, diceva
"scansione fallita" e chiedeva conferma a ogni commit. Un segreto dentro quel file la guardia lo trova
ancora.

**Il principio**: una conferma chiesta a vuoto insegna a dire sì senza leggere. La telemetria ne ha
contate otto fra il 25 e il 27/10 su un'installazione sola.

---

## 2026-10-28 — Il lavoro di un worktree non resta indietro, e /inizio trova le cartelle col trattino basso

**Cosa cambia**: se una sessione ha lavorato in una copia a parte (un worktree) e i suoi commit non
sono tornati nella cartella principale, `/inizio` te lo dice in cima, col numero dei commit, e propone
di riportarli. `/fine` prova anche il merge quando il fast-forward non basta, e prima dell'handoff
controlla che il ramo sia davvero unito: se non lo è, te lo dice nella chiusura (segnalazione n. 20).
`/inizio mio-progetto` trova la cartella `mio_progetto` (segnalazione n. 21). Con la cartella dei
progetti scritta come `~/Progetti`, un progetto nuovo nasce lì e non in una cartella chiamata `~`
(segnalazione n. 19). `/diagnosi` non propone più di mettere nel repository cache, dipendenze e le
copie di lavoro di Claude Code (segnalazione n. 22).

**Il principio**: il lavoro fatto non deve sparire in silenzio. Un ramo non unito è lavoro che nessuno
vede: lo deve vedere chi apre la sessione dopo.

## 2026-10-28 — Il resto delle domande del Computer Club: sessioni dal pannello, segnalazioni seguite, skill proposte

**Cosa cambia**: dal pannello `/dafare` il tasto `o` apre una finestra nuova del terminale con Claude
già partito sul todo scelto (`/inizio progetto -- il todo`), su Mac, Windows e Linux. Prima di aprire
controlla che il numero indichi ancora il todo che vedi: dopo un merge che ha rinumerato i todo si
ferma, invece di partire su quello sbagliato. `/segnala stato`
ti dice a che punto sono le tue segnalazioni: in attesa, arrivate col loro numero, o corrette, con la
novità che lo racconta; `/novita` ti avvisa quando esce la correzione di una tua. `/proponi` porta a chi
mantiene Arturo una skill che hai scritto tu: la ripulisce con te da nomi e dati, ti mostra il testo e
parte solo dopo il tuo sì. Prima di un ultracode, Claude ti dice quanto costa e quanta quota ti resta.

**Il principio**: ogni pezzo risponde a una domanda fatta alla sera del 27/10: "clicco e vado avanti",
"quando faccio il segnale cosa succede?", "come la faccio arrivare agli altri?", "quanto mi è costato?".
Una promessa che nessun codice manteneva ("/novita la racconta con quel numero") ora ha il suo codice.

**Da sapere**: una segnalazione partita in differita ora tiene il suo numero; le correzioni nate da una
segnalazione la citano sempre come "segnalazione n. X". Della skill proposta esce solo il testo che hai
letto, come per `/segnala`: nessun file parte da solo.

## 2026-10-28 — Meno conferme quando Claude legge il web con uno script

**Cosa cambia**: uno script che legge pagine o servizi web, per esempio per cercare su archive.org una
copia dei link morti, non ti chiede più "Invio di dati (POST/upload)". La guardia anti-esfiltrazione
chiede conferma solo quando un file del tuo computer parte verso un server esterno (un upload con
`curl -F @file`), o quando un comando apre un canale di rete grezzo (`nc`, `/dev/tcp`). Il resto lo
giudica il classificatore di auto mode, che legge lo script e capisce se legge o se porta fuori dati.

**Il principio dietro**: una guardia chiede solo dove la forma del comando basta a decidere. Dove serve
capire cosa fa il codice, decide chi lo legge.

**Da sapere**: la conferma arrivava anche sulla sola lettura, e chi la vede dieci volte al giorno impara
a rispondere sì senza leggere. Se usi auto mode, il controllo resta: lo fa il classificatore.

---

## 2026-10-28 — Le domande della sera del Computer Club

**Cosa cambia**: la barra in basso scrive la quota in parole, "5 ore" e "settimana", e dice sempre a
che ora si azzerano le 5 ore. `/guidami` legge la quota: se ne avanza molta e l'azzeramento è vicino,
te lo dice e mette in cima i lavori lunghi che Claude può fare mentre tu fai altro. Se chiedi cos'è il
contesto, che differenza c'è tra git e GitHub, cos'è un branch, cosa succede alle tue modifiche quando
Arturo si aggiorna, cos'è un subagent o ultracode, Claude risponde in poche frasi e ti dice dove trovi
la cosa in Arturo. Quando `/segnala` arriva, ti dice il suo numero: è quello con cui la correzione
compare qui. Una segnalazione rimasta in attesa parte alla sessione dopo da sola, senza portarsi dietro
i dati d'uso prima delle 6 ore.

**Il principio dietro**: una domanda che torna tre volte a voce è una funzione che manca.

**Da sapere**: sono le domande fatte alla terza sera del Computer Club, il 27/10, da chi usava Arturo da
una settimana. Il pannello `/dafare` c'era già: ora il riepilogo di `/setup` lo presenta, insieme alla
barra e al suono di quando Claude ti aspetta.

---

## 2026-10-27 — /fine non lascia archivi a metà, e /segnala dice perché non è partita

**Cosa cambia**: se usi Arturo senza un tuo repository remoto, `/fine` toglie dal tracciamento di git
gli handoff, i todo e la memoria che erano già tracciati, e li lascia sul disco come sono. Prima la
pulizia degli handoff lasciava file cancellati e non salvati, che a ogni sessione sembravano lavoro in
sospeso. Se hai un remoto tuo, non cambia niente. Quando `/inizio` apre una copia a parte del progetto,
Claude scrive anche i testi lunghi dei comandi in una forma che Claude Code accetta. Se un'installazione
chiede la password del Mac (un comando con `sudo`), Claude non te lo passa più col prefisso `!`, dove
la password non si può scrivere: cerca prima una strada senza password, poi ti chiede di usare il
Terminale. Quando `/segnala` non riesce a inviare, il messaggio dice il codice che ha risposto il
server, oppure che la rete non ha risposto.

**Il principio dietro**: un errore che non dice la sua causa costa due volte, a te e a chi lo deve
correggere.

**Da sapere**: lo mostravano le segnalazioni n. 14, 15 e 16. Se una tua segnalazione non è partita,
rimandala dopo l'aggiornamento: il messaggio ci dirà dove si ferma.

---

## 2026-10-26 — L'aggiornamento non si ferma sui tuoi appunti, e un worktree non perde file

**Cosa cambia**: l'aggiornamento automatico parte anche se i tuoi archivi (handoff, todo, memoria)
hanno modifiche non salvate. Con Arturo come origin, la pulizia degli handoff di `/fine` lasciava file
cambiati, e quei file fermavano l'aggiornamento a ogni sessione. Ora quegli archivi restano come li hai
lasciati, e solo un file di Arturo cambiato ferma l'aggiornamento. Quando `/inizio` apre la sessione in
una copia a parte del progetto (un worktree, perché un'altra sessione lavora nella stessa cartella),
`/fine` riporta nella cartella principale anche i file che git ignora, come una cartella `lavoro/`.
Prima la rimozione della copia li cancellava senza avviso. `/inizio` dice anche come scrivere i comandi
nella copia: uno per volta, con i cicli in uno script, perché Claude Code rifiuta quelli che non sa
leggere. `/setup` ha una fase facoltativa in più, solo su Mac: Lancillotto annota in locale quali app e
file usi, e dopo tre giorni Arturo ti propone fino a tre lavori che può fare lui. La guardia delle
scritture vede più comandi, fra cui `tar -x`, `unzip -d`, `patch`, `git apply` e `git stash pop`.

**Il principio dietro**: un file tuo non si cancella e non ti blocca in silenzio, neanche quando sta
fuori da git.

**Da sapere**: lo mostravano le segnalazioni n. 13 e n. 14. Se il tuo aggiornamento automatico era
fermo, si sblocca con questo rilascio, perché la procedura si legge dal rilascio in arrivo. Se
Lancillotto non ti interessa, `/setup` salta la fase.

---

## 2026-10-24 — La telemetria manda meno, e conta meglio i tuoi sì

**Cosa cambia**: dalla telemetria esce meno di prima. Se un aggiornamento va in conflitto su un file
tuo, per esempio una skill che hai scritto tu, esce solo `file:altro`, mai il nome del file. Se una
guardia ferma un commit con un segreto, esce la famiglia del segreto, come `segreto-cloud`, e non più il
servizio, come `google-api-key`. Un comando tuo conta come `altro`, senza il nome. Delle guardie escono
solo i nomi di Arturo, da un elenco chiuso. Come versione esce solo il rilascio di Arturo: un tag tuo non esce. Un sì a una guardia conta anche su Monitor e quando il
comando poi fallisce: prima contava come un no. Il README non dice più che l'id è "non legato a te", e
la nuova pagina [`docs/privacy.md`](docs/privacy.md) dice chi tiene i dati, per quanto e come li cancelli.

**Il principio dietro**: la promessa del README deve dire esattamente ciò che esce. Un nome di file o
di servizio dice qualcosa di te, e un numero sbagliato porta a correggere la cosa sbagliata.

**Da sapere**: alla prima sessione Arturo ti avvisa di nuovo, perché cosa esce è cambiato. L'id è
casuale, ma chi mantiene Arturo può sapere quale persona c'è dietro se la conosce: per questo i dati non
sono anonimi. Le segnalazioni restano sul server 12 mesi, e di una segnalazione Telegram ed email ricevono solo il
numero, l'origine e il tipo. Cosa arriva su Telegram e per email, in tutto, lo dice `docs/privacy.md`. La spegni come sempre con `python3 ~/.claude/bin/arturo telemetria spegni`.

---

## 2026-10-23 — Un progetto riservato resta fuori dal sync

**Cosa cambia**: se togli dal sync gli appunti di un progetto, con una riga nel `.gitignore` della tua
config, `/fine` la rispetta. Prima li aggiungeva lo stesso e li avrebbe mandati al tuo repository
privato al primo sync. Gli appunti degli altri progetti viaggiano come prima, solo verso un repository
privato.

**Il principio dietro**: una scelta che fai tu sulla tua config vale più di una regola generale di
Arturo.

**Da sapere**: lo mostrava la segnalazione n. 12. Insieme agli appunti restano fuori anche i file
`.key` e `.env`, che il `.gitignore` di Arturo esclude già.

---

## 2026-10-23 — Claude ti ricorda di finire /setup, e una reinstallazione non perde niente di tuo

**Cosa cambia**: se hai installato Arturo e non sei arrivato in fondo a `/setup`, Claude te lo dice in
una riga all'inizio della sessione, una volta al giorno. Puoi rispondere di no: l'invito torna il giorno
dopo, e smette quando `/setup` arriva in fondo. Se reinstalli Arturo da capo coi comandi del README,
tornano al loro posto il tuo `CLAUDE.md`, `personale/`, la memoria, i todo e le tue scelte. Fra le
scelte c'è la telemetria spenta, che prima una reinstallazione riaccendeva. Arturo ora si installa
anche con una riga sola: `curl -fsSL https://arturo.stellakamikaze.org/installa.sh | bash`. Se Arturo
c'è già, la riga si ferma e ti dice di scrivere `/aggiorna`.

**Il principio dietro**: la telemetria ha mostrato installazioni nuove che non hanno mai aperto `/setup`,
o che si sono fermate a metà. Senza la configurazione Arturo non sa chi sei né dove stanno i tuoi progetti.

**Da sapere**: chi ha installato Arturo prima del 16 ottobre non riceve l'invito, perché allora `/setup`
non lasciava il segno di essere finito.

---

## 2026-10-22 — L'avviso sulla telemetria torna, e l'unione regge dopo un conflitto

**Cosa cambia**: alla prossima sessione Arturo ti ridice in due righe cosa manda la telemetria, perché
ora c'è una cosa in più: quando `block-dangerous` o `commit-secret-gate` ti chiedono conferma, esce anche
il nome della regola.
Se un aggiornamento si ferma su un conflitto vero e lo risolvi con `/aggiorna`, il resto
dell'aggiornamento continua a unire `settings.json` come impostazioni. Prima, dopo il primo conflitto,
tornava a unirlo riga per riga. `/diagnosi`, `/segnala`, `/aggiorna`, `/novita` e `/setup` scrivono i
percorsi con la tilde (`~/.claude`), che Claude Code accetta anche quando la sessione lavora in un worktree.

**Il principio dietro**: quando cambia cosa esce dal tuo computer, lo devi sapere da Arturo prima che
da un riepilogo.

**Da sapere**: della regola esce solo il nome, come `rm-cartella` o `google-api-key`, mai il file o la chiave. Gli hook che `/setup` ti riporta
da prima di Arturo restano dove l'altra app li aveva messi, e `/fine` li salva con `settings.json`.

---

## 2026-10-22 — Aggiornamenti senza conflitti sulle impostazioni

**Cosa cambia**: quando Arturo e tu, o un'app come iTerm2, cambiate tutti e due `settings.json`,
l'aggiornamento unisce le due versioni come impostazioni e non più riga per riga. Un hook in più di
qua e un permesso in più di là stanno insieme, e l'aggiornamento non si ferma. Se tutti e due avete
cambiato la stessa impostazione in modo diverso, resta il conflitto di prima e `/aggiorna` lo risolve
con te. Quando una guardia ti chiede conferma, la telemetria registra anche quale regola ha chiesto.

**Il principio dietro**: il 21/10 tutti e due gli aggiornamenti si sono fermati su `settings.json`, per
modifiche che non si toccavano.

**Da sapere**: della regola esce solo il nome (per esempio `rm-cartella`), mai il comando o il percorso.

---

## 2026-10-22 — Gli hook che avevi tornano, e tre segnalazioni chiuse

**Cosa cambia**: se prima di Arturo un'altra app aveva aggiunto i suoi hook a Claude Code (ClaudeBar,
una barra di stato, un notificatore), `/setup` li ritrova nella cartella messa da parte
all'installazione e, col tuo sì, li rimette. Lo fa `python3 ~/.claude/bin/arturo personale
hook-precedenti`, che puoi lanciare anche adesso. In modalità auto, dopo il tuo sì a una modifica del
CLAUDE.md, Claude può sbloccarla da solo: prima dovevi lanciare tu il comando con `!`. L'avviso DERIVA
non conta più un file che ha cambiato solo i permessi, e `/setup` non li cambia più. `/inizio` e
`/fine` funzionano anche quando la sessione lavora in una copia separata del progetto (un worktree).

**Il principio dietro**: Arturo si aggiunge a quello che c'è. Non deve togliere niente in silenzio.

**Da sapere**: lo sblocco automatico vale solo per il CLAUDE.md e solo dopo il tuo sì a quella
modifica. Per le impostazioni e gli hook di Claude Code il comando resta tuo. Se l'avviso DERIVA
ti segnalava guardie modificate senza differenze nel contenuto, dalla prossima sessione sparisce.

---

## 2026-10-21 — Meno conferme inutili, /dafare ricorda la barra, gli aggiornamenti dicono cosa li blocca

**Cosa cambia**: le guardie non chiedono più conferma per cancellare una cartella appena creata con
`mktemp`, né per uno script che legge un JSON dopo una richiesta verso il tuo computer o che importa
`urllib.request`. Chiedono invece quando uno script python manda un file con `curl` scritto come lista
di argomenti (`subprocess.run(['curl', '-d', '@file', ...])`), che prima passava senza conferma. `/dafare
nascondi` resta valido anche dopo `/clear` e `/resume`. Se un aggiornamento si ferma per un
conflitto, Arturo annota quale file lo blocca, così il problema si corregge più in fretta.

**Il principio dietro**: una conferma che non protegge niente insegna a dire sì senza leggere.

**Da sapere**: della telemetria escono solo i percorsi dei file di Arturo in conflitto, mai il
loro contenuto. È la stessa forma che usa già la deriva.

---

## 2026-10-20 — Arturo lavora come chi lo mantiene: /inizio, /fine e lo stile Conciso

**Cosa cambia**: `/inizio` ti mostra il lavoro per filone, con chi deve agire ("Faccio io",
"Preparo io, poi tu", "Decidi tu"), e rispondi a parole invece che da un menu. Con `-- compito`
Claude ti mostra prima come ha capito la richiesta. Se un'altra sessione lavora sullo stesso
progetto, `/inizio` se ne accorge e lavora in una copia separata. `/fine` non corregge più niente
all'ultimo momento: un test rosso o un pezzo mancante diventa un todo, e il lavoro fatto in una
copia separata torna nel progetto. Lo stile di partenza è Conciso: risposte brevi, prima l'esito.
Lo stile Guida e l'agente doc-reviewer escono.

**Il principio dietro**: chi mantiene Arturo usa ogni giorno questi comandi. Se i tuoi fossero
diversi, i loro difetti resterebbero invisibili a chi può correggerli.

**Da sapere**: se avevi scelto lo stile Guida, dalla prossima sessione vale quello standard di
Claude Code. Per tornare a uno stile breve scrivi `/output-style` e scegli Conciso.

---

## 2026-10-20 — La memoria è la stessa di chi mantiene Arturo

**Cosa cambia**: la memoria facoltativa di Arturo ora è Melchior, la memoria che chi mantiene
Arturo usa ogni giorno: lo stesso codice, copiato identico. Le tue note restano dove sono e come
sono: quelle che Claude Code scrive da solo, le cartelle che hai aggiunto, e una cartella nuova,
`~/.claude/data/memory/`, per le note che curi tu (fuori da git, come i todo). Il richiamo trova
anche due note con lo stesso nome in due progetti, e non conta due volte una nota raggiunta da due
posti. All'avvio, se c'è, Claude riceve la scheda del progetto in cui lavori. Il controllo sulle
note che Claude scrive guarda anche gli URL che portano dati fuori, e fida gli host che hai messo
in `hooks/hosts-interni.local`. La memoria resta spenta finché non la accendi.

**Il principio dietro**: chi mantiene Arturo deve usare quello che usi tu. Con due memorie diverse,
i difetti della tua restano invisibili a chi la mantiene. Le sue note invece non arrivano a te:
nel repository c'è solo il codice.

**Da sapere**: niente da fare. `arturo memoria stato` dice dove cerca e quante note trova, e
`arturo memoria accendi` la accende. Se ci sono parole che il richiamo deve ignorare, scrivile una
per riga in `hooks/melchior-stopword.local`.

---

## 2026-10-20 — Meno domande inutili, meno uscite nascoste, e l'installazione non ti fa perdere niente

**Cosa cambia**: Claude ti chiede conferma meno spesso dove non serve. Copiare una cartella con
`--exclude .env` o cancellare una cartella temporanea appena creata non chiedono più niente.
Chiedono invece alcuni modi nascosti di mandare dati fuori, che prima passavano: un comando dentro
lo user-agent o il referer di `curl`, un `curl` dentro un `echo`, `requests` in Python. Lo stesso per alcune
forme di `git clean` e di cancellazione di cartelle da Python che prima sfuggivano. Chi installa
Arturo su un Claude Code già usato non perde più login, sessioni passate, cronologia e plugin: dopo
il download tornano al loro posto. `/diagnosi` controlla anche l'installazione di Claude Code e i
test dei mod, e la guida spiega `claude --safe-mode`. Nel Terminale di macOS l'avvio non chiede più
il permesso di Automazione per il titolo della finestra.

**Il principio dietro**: una domanda inutile insegna a rispondere sì senza leggere. Le guardie
devono fermarsi dove c'è un rischio vero e tacere altrove. E un'installazione non deve costarti il
lavoro che avevi già.

**Da sapere**: niente da fare. Se un aggiornamento non si installa da solo, adesso chi mantiene
Arturo vede il motivo (un'altra sessione aperta, la firma, la versione) e può correggerlo.
Con Chrome aperto e l'estensione Claude in Chrome attiva, l'aggiornamento automatico non partiva
mai: Arturo scambiava il ponte con Chrome per una sessione aperta. Ora lo riconosce. E se un'altra
sessione aperta rimanda davvero l'aggiornamento, l'avvio dopo te lo dice, con il modo di
installarlo subito.

---

## 2026-10-19 — Se manca node, la barra in basso te lo dice

**Cosa cambia**: la barra in basso mostra il modello, quanto contesto hai usato e la quota del tuo
abbonamento. È uno script che gira con node. Claude Code oggi si installa anche senza node, e su un
computer appena preparato la barra restava vuota senza dire perché. Ora, se node manca, la barra
scrive "Arturo: manca node" e l'avvio della sessione lo dice a Claude, che ti aiuta a installarlo.
Lo stesso vale per l'avviso che ti dice quando il contesto sta per finire.

**Il principio dietro**: uno strumento che si spegne in silenzio sembra funzionare. Se qualcosa
non può partire, Arturo lo dice nel punto dove lo stai cercando.

**Da sapere**: node si scarica da nodejs.org (l'installer per Mac è un file .pkg). Dopo
l'installazione chiudi e riapri Claude Code. Se la barra resta vuota anche con node, dillo con
`/segnala`.

---

## 2026-10-19 — Claude Code torna con tutte le sue funzioni, e le guardie vedono anche Monitor

**Cosa cambia**: Arturo non spegne più la telemetria di Claude Code. Quando era spenta, Claude Code
smetteva anche di scaricare le impostazioni delle sue funzioni, e ne perdevi alcune senza saperlo.
Tra queste c'è il segno sui testi incollati, che aiuta Claude a non scambiare per tue le istruzioni
scritte da altri. Le altre sono l'esclusione dei collegamenti rotti che bloccavano ogni richiesta,
la compattazione della conversazione mentre sei via e `/skill-doctor`, che dice quali skill non usi.
Con le funzioni accese arriva anche Monitor, lo strumento con cui Claude segue un comando in
background: le guardie ora controllano anche i suoi comandi. In più una guardia che non riesce a
partire ferma l'azione invece di lasciarla passare.

**Il principio dietro**: Arturo non deve togliere a chi lo usa le difese che Claude Code ha già.
Spegnere la telemetria di Claude Code era una scelta presa all'inizio e mai spiegata, e costava più
di quanto proteggeva. Secondo Anthropic quegli eventi non contengono codice, percorsi dei file o
comandi. Una guardia che si rompe in silenzio è peggio di una guardia che ti ferma per sbaglio.

**Da sapere**: se vuoi la telemetria di Claude Code spenta lo stesso, "Cosa non è neutro" nel
README spiega come e cosa perdi. Su Windows lo strumento PowerShell resta spento, perché le guardie
di Arturo controllano solo Git Bash. Con Claude Code più vecchio della 2.1.300 `/setup` ti chiede di
aggiornarlo.

---

## 2026-10-19 — Conferma per le ricerche che eseguono programmi, e Sonnet di riserva

**Cosa cambia**: tre comandi di ricerca e lettura (`rg`, `sed -n` e `find`) non sono più approvati
in blocco. Quando cercano o leggono, passano senza domanda come prima. Quando eseguono un programma
o riscrivono un file, Claude ti chiede conferma. Due esempi: `rg --pre`, che passa ogni file a un
programma, e `sed -n -i`, che modifica il file sul posto. Prima passavano senza domanda. In più, se
il modello principale è sovraccarico, Claude continua con Sonnet invece di fermarsi con un errore.

**Il principio dietro**: una regola che approva un comando intero approva anche le sue forme
pericolose. Claude Code riconosce già da solo le forme che leggono e basta, quindi la regola larga
aggiungeva solo il rischio. Un errore di sovraccarico, per chi inizia, sembra un guasto: con un
modello di riserva il lavoro va avanti.

**Da sapere**: niente da fare.

---

## 2026-10-19 — La scheda del terminale anche sul Mac, e niente falsi rossi da igiene e iTerm2

**Cosa cambia**: sul Mac la scheda del terminale ora cambia davvero titolo e colore: prima restava
ferma. Nel Terminale di Apple, che non colora le schede, il titolo comincia con "● TOCCA A TE" quando
Claude aspetta te, e la scheda in secondo piano mostra la campanella. Il controllo di igiene su
GitHub gira solo sul repository pubblico di Arturo. Se salvi la tua `~/.claude` in un repository
privato, non ricevi più l'email "Run failed: igiene" a ogni `/fine`. E se un programma aggiunge a
`settings.json` hook suoi senza `matcher` (lo fa iTerm2 con `cc-status`), l'avvio non dice più
"una guardia potrebbe non proteggere".

**Il principio dietro**: con più sessioni aperte devi vedere da fuori quale ti aspetta, senza
entrare in ogni scheda. E un avviso falso insegna a ignorare quelli veri. Il controllo di igiene cerca
i nomi dell'autore di Arturo, e nei tuoi appunti non ha niente da cercare. Un hook senza `matcher` è
lecito per Claude Code, e le guardie di Arturo restavano al loro posto.

**Da sapere**: niente da fare. Le correzioni su igiene e iTerm2 vengono dalle vostre segnalazioni con `/segnala`.

---

## 2026-10-17 — Solo rilasci firmati, anche con /aggiorna, e guardie che vedono di più

**Cosa cambia**: `/aggiorna` installa solo l'ultimo rilascio firmato da chi mantiene Arturo, come
l'aggiornamento automatico, e mai le modifiche pubblicate dopo. Se l'ultimo rilascio non ha una firma
valida, l'avvio, la barra in basso, `/inizio` e `/novita` dicono "possibile compromissione: non
aggiornare, segnala a chi mantiene Arturo", e `/aggiorna` non installa niente, neanche col tuo sì. In
più Claude ti chiede conferma prima di: leggere un file `.env` (dove stanno le chiavi dei servizi),
cancellare una cartella con `shutil.rmtree` o i file non salvati in git con `git clean -f`, allineare
una cartella con `rsync --delete`, mandare dati fuori con un `curl` che costruisce l'indirizzo con un
comando, una pipe verso `nc` o il codice di `node` e `python` che chiama la rete.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer. Prima la firma
proteggeva solo l'aggiornamento automatico: proprio quando un rilascio non era firmato, l'avviso ti
mandava a `/aggiorna`, che lo installava lo stesso. Una firma che manca è il segno che qualcosa non
va, e la risposta giusta è fermarsi e dirlo. Le guardie nuove seguono la regola di sempre: chiedono
dove un errore non si annulla, e restano zitte sul lavoro normale. Un `curl` qualsiasi, un `rsync`
senza `--delete`, `git clean -n` e la cartella `build/` passano senza domande.

**Da sapere**: niente da fare. Se vedi "possibile compromissione", non cercare un'altra strada per
aggiornare: segnalalo con `/segnala`, o in privato come dice `SECURITY.md`. Per controllare la firma
servono git 2.34 e OpenSSH 8.2, o più recenti: con versioni più vecchie Arturo non si aggiorna e lo
dice, senza parlare di compromissione.

Corretto anche un guasto segnalato da chi usa Arturo: se avevi aggiunto righe a
`hooks/session-start.sh` o `session-end.sh`, `/aggiorna` diceva di averle spostate in
`~/.claude/personale/`, ma il file non arrivava e le righe si perdevano. Ora arrivano, commentate come
sempre. Se dopo un aggiornamento ti manca qualcosa all'avvio, chiedi a Claude di ritrovarlo nella
versione di prima: `/aggiorna indietro` sa qual è.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

---

## 2026-10-16 — Arturo si aggiorna da solo, come Claude Code

**Cosa cambia**: non serve più `/aggiorna`. Quando esce una versione nuova, la barra in basso di
Claude Code te lo dice ("↑ Arturo … · si installa alla chiusura"). Quando chiudi la sessione, Arturo
la installa da solo, con la stessa procedura di `/aggiorna`: le tue aggiunte restano tue, e se
qualcosa non torna non cambia niente. Se hai più sessioni aperte, la installa l'ultima che chiudi.
Alla sessione dopo Claude ti dice a che versione sei arrivato, e `/novita` ti racconta cosa cambia.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer. Per questo
si installano da soli solo i rilasci firmati con la chiave di chi mantiene Arturo, e la firma si
controlla con la chiave che hai già: un repository manomesso non basta. Se la firma manca, o la
storia pubblicata è stata riscritta, Arturo non installa niente e te lo dice.

**Da sapere**: preferisci leggere ogni aggiornamento prima? Scrivi a Claude "tieni gli
aggiornamenti a mano", oppure lancia `python3 ~/.claude/bin/arturo aggiornamenti manuali`: resta
l'avviso, e aggiorni con `/aggiorna` come prima. Questa è l'ultima volta che serve `/aggiorna` per
ricevere una versione: da qui in poi arrivano da sole. La telemetria conta a parte gli
aggiornamenti installati da soli (l'esito `automatico` dell'evento `aggiorna`): per questo
all'avvio Claude ti ripete una volta cosa esce.

---

## 2026-10-16 — L'avvio e la chiusura personali non bloccano più gli aggiornamenti

**Cosa cambia**: se hai aggiunto righe all'avvio o alla chiusura della sessione
(`hooks/session-start.sh`, `hooks/session-end.sh`), ogni aggiornamento di Arturo che toccava quei
file andava in conflitto e si fermava. Adesso `/aggiorna` sposta le tue righe in un file tuo,
`~/.claude/personale/session-start.sh` (o `session-end.sh`), che l'hook di Arturo esegue alla fine e
che nessun aggiornamento tocca. Le righe arrivano commentate: Claude le rilegge con te e toglie il
`#` a quelle che devono girare. Se invece hai modificato una delle guardie di sicurezza, l'avvio
adesso te lo dice a parte. Claude ti mostra cosa cambia e, se vuoi, la rimette com'è in Arturo con
`arturo personale ripristina`. Al server di Arturo il riepilogo del lunedì dice anche quante
installazioni nuove non hanno mai lanciato `/setup`.

**Il principio dietro**: le tue aggiunte restano tue senza fermare gli aggiornamenti. Una guardia
allentata è una tua scelta, ma la fai sapendolo. Sono le prime correzioni nate dal ciclo del
lunedì, che legge la telemetria e propone a chi mantiene Arturo cosa sistemare.

**Da sapere**: niente da fare. Se avevi modificato l'avvio, al prossimo `/aggiorna` Claude ti
propone di rileggere le righe spostate.

---

## 2026-10-16 — Le tue skill restano tue, e /setup ti riconosce

**Cosa cambia**: quando `/fine` salva la config verso il tuo repository, le skill nuove che hai
creato con `/creaskill` partono solo se il repository è privato. Se non risulta privato, restano
su questo computer e Claude ti chiede se pubblicarle: una skill tua può contenere dati tuoi.
`/diagnosi` ti dice anche quando un tuo file in `personale/` appartiene a un comando che Arturo
non ha più, come `/strato`: nessuno lo legge, e puoi tenerlo da parte o cancellarlo. Se avevi
finito `/setup` prima di oggi e lo rilanci, Arturo ti riconosce e ti propone la verifica invece
della prima configurazione. Su Windows la telemetria registra anche le conferme dei comandi con
caratteri speciali, e un `rm -rf` nella cartella temporanea di Windows non chiede più conferma,
come `/tmp` sul Mac.

**Il principio dietro**: niente di tuo esce senza un tuo sì, e niente ti fa rifare un lavoro già
fatto.

**Da sapere**: niente da fare.

---

## 2026-10-16 — Su Windows le guardie leggono tutto il comando

**Cosa cambia**: su Windows alcune guardie di Arturo leggevano male i comandi con caratteri
speciali, e in quei casi lasciavano passare senza chiedere. Un `rm -rf` su una cartella con una
virgoletta tipografica (`”`) nel comando passava senza conferma. Un invio di email con una
freccia ("→") partiva senza conferma. Adesso ogni guardia legge il comando intero, con gli
accenti e i simboli, e ti chiede conferma come sul Mac. Su Windows è corretto anche `/fine`:
un file già salvato in un repository, in una sottocartella, non risulta più da scartare. Lo
scratchpad di Claude adesso conta come cartella temporanea. La memoria trova anche le note
con parole accentate.

**Il principio dietro**: una guardia che si confonde deve chiedere, non tacere. E una correzione
vale solo se un controllo la prova anche sul sistema dove il guasto è nato.

**Da sapere**: niente da fare. Sul Mac non cambia niente. Se provi Arturo in una cartella
temporanea, da lì la telemetria non parte più verso il server di Arturo: parte solo verso un
server che indichi tu con `ARTURO_TELEMETRIA_URL`.

---

## 2026-10-16 — La scheda del terminale dice il progetto e lo stato

**Cosa cambia**: il titolo della scheda in cui gira Claude Code ora dice su quale progetto lavora.
In Windows Terminal e in iTerm2 il colore della scheda dice lo stato: verde quando Claude aspetta
te, giallo mentre lavora, rosso quando il turno si è fermato per un errore, come un'API giù o un
limite raggiunto. Negli altri terminali lo stato è scritto nel titolo, per esempio "romanzo · al
lavoro". Il progetto è quello scelto con `/inizio`, altrimenti il repository o la cartella
in cui hai aperto Claude Code. Il titolo automatico di Claude Code, quello col riassunto della
conversazione, non c'è più: al suo posto c'è il progetto.

**Il principio dietro**: con tante schede aperte, guardare deve bastare a sapere dove serve una
tua risposta.

**A chi serve**: a chi tiene aperte più sessioni insieme.

---

## 2026-10-16 — Nove comandi, una diagnosi del progetto, e le tue skill con /creaskill

**Cosa cambia**: Arturo ti racconta e ti propone nove comandi: `/inizio`, `/fine`, `/aggiorna`,
`/novita`, `/segnala`, `/setup`, `/guidami`, `/diagnosi` e il nuovo `/creaskill`. Tutto il resto
lo usa Claude da solo, dentro questi: lo sparring, la scrittura semplificata, il brief, i todo,
l'audit. `/setup` adesso fa anche la verifica di una configurazione già fatta: scrivi
`/setup verifica`. `/diagnosi` non guarda più solo il codice ma il progetto intero: controlla
che Arturo regga, lo stato di git, handoff e todo, i file citati negli handoff che non esistono
più, e i materiali sparsi in Download o fuori dal repo, con un posto proposto per ognuno.
`/creaskill` ti fa quattro domande e trasforma un lavoro che fai spesso in una skill tua.

Escono cinque comandi: `/strato` (lo strato delle organizzazioni torna più avanti, rifatto),
il percorso a tappe con `/percorso` e `arturo percorso`, `/progetto`, `/discovery` e
`/write-plan`. Un progetto nuovo lo crei con `/inizio <nome>`: se non esiste, Claude ti chiede
se crearlo.

**Il principio dietro**: pochi comandi che si raccontano bene valgono più di tanti che si
dimenticano. Un comando che nessuno lancia è un comando che nessuno mantiene.

**Da sapere**: se hai aggiornato con `/aggiorna`, i file tolti spariscono da soli. Se avevi
modificato uno dei comandi tolti, `/aggiorna` te lo chiede. Se copi le cartelle a mano, cancella
tu `commands/strato.md`, `commands/progetto.md`, `commands/discovery.md`,
`commands/write-plan.md`, la cartella `skills/percorso/`, `bin/percorso.py`, `docs/esercizi.md`,
`docs/referente.md` e la cartella `templates/`. Il file `session-env/percorso.json` non serve
più e si può cancellare. Se nei tuoi todo c'è il progetto `_percorso`, sono gli esercizi del
percorso: chiedi a Claude di scartarli. Se avevi installato lo strato di un'organizzazione,
resta installato ma non si aggiorna più da solo: `claude plugin list` lo mostra, e
`claude plugin uninstall` lo toglie.

---

## 2026-10-16 — In vista solo i comandi di ogni giorno, Impeccable dal setup, esce blast-radius

**Cosa cambia**: Claude ti propone di sua iniziativa solo i comandi che servono ogni giorno o quando serve:
`/inizio`, `/fine`, `/aggiorna`, `/novita`, `/segnala`, `/setup`. Gli altri (`/guidami`, `/sparring`,
`/progetto`, `/discovery`, `/write-plan`, `/diagnosi`, `/strato`, `/percorso`, `/italiano-semplificato`)
restano tutti: li lanci tu scrivendo il nome. Il README li divide in "Ogni giorno", "Quando serve" e
"Gli altri comandi". In più `/setup` ti propone Impeccable (fase 8c), la skill di design delle
interfacce di Paul Bakaus: la installa dall'autore, con le sue versioni nuove. Esce il mod
`blast-radius`: fermava ogni `rm -rf` e aspettava una risposta, e quando la risposta non arrivava
bloccava anche il lavoro utile scritto nello stesso comando.

**Il principio dietro**: chi comincia ha bisogno di due comandi, non di quindici. Un elenco lungo
fa sembrare difficile anche quello che è semplice. E una guardia che ferma il lavoro più spesso di
quanto lo protegga va tolta.

**Da sapere**: niente da fare. Prima di cancellare una cartella Claude ti chiede ancora conferma
(`block-dangerous`), e il push forzato resta vietato. "A che punto sono?" non apre più da solo il percorso: scrivi `/percorso`.
Se fai siti o pagine e vuoi Impeccable senza rifare tutto il setup: `/setup` e salta alla fase 8c,
oppure leggi `docs/impeccable.md`.

---

## 2026-10-15 — Gmail, Calendar e Drive senza Google Cloud, e guardie con gli accenti

**Cosa cambia**: per collegare la posta, il calendario e i documenti non serve più creare un
progetto su Google Cloud. `/inizio gws` ti propone prima i connettori di claude.ai: li attivi dal
browser, riapri Claude Code e ci sono. La strada vecchia resta per chi usa più account Google. In
più i messaggi delle guardie scrivono "c'è" e "già" con gli accenti veri, non con l'apostrofo.

**Il principio dietro**: il primo collegamento deve stare nei cinque minuti. Se costa un'ora di
pagine in inglese, chi comincia si ferma lì.

**A chi serve**: a chi non ha ancora collegato Google. Scrivi `/inizio gws` dopo il prossimo
`/aggiorna`.

---

## 2026-10-15 — Guardie che non perdono il filo, e il brief su ogni richiesta

**Cosa cambia**: una review di Arturo ha trovato comandi che la shell esegue e che le guardie non
vedevano: un `<<` scritto dentro virgolette, un delimitatore come `'E'OF`, un testo mandato a
`/bin/bash` o scritto in un file e poi eseguito. Ora una guardia toglie il testo di un heredoc solo
quando i confini sono certi e il testo va a un lettore come `cat`: nel dubbio lo controlla. In
modalità auto il controllo di sicurezza di Claude Code tiene anche le sue regole di serie, `gh` è
libero solo in lettura (un `gh gist create --public` passa dal giudizio) e una lettura di
`~/.claude/data/credentials/` chiede conferma. Il brief torna su ogni richiesta di lavoro, anche
breve: per una richiesta piccola bastano tre righe.

**Il principio dietro**: il testo che una guardia toglie è testo che non controlla. Meglio una
domanda in più che un comando che passa senza essere visto.

**A chi serve**: a tutti, senza fare niente: arriva col prossimo `/aggiorna`.

---

## 2026-10-15 — Le tue modifiche ai comandi si mettono da parte da sole

**Cosa cambia**: se hai modificato un comando di Arturo (per esempio hai aggiunto a `/inizio` la
tabella dei tuoi progetti) e l'aggiornamento cambia lo stesso comando, `/aggiorna` sposta da solo le
tue righe in un file tuo, `~/.claude/personale/inizio.md`. Il comando torna quello di Arturo e non
va più in conflitto. Quando lanci `/inizio`, Claude legge anche le tue righe, quindi il comando fa
tutto quello che faceva prima. Non devi fare niente: Claude te lo dice in una frase. Lo spostamento
avviene nella copia di prova: se l'aggiornamento non va in porto, la tua config non cambia. Se hai un
tuo repository della config, deve essere privato: solo così `personale/` viaggia fra le tue macchine.
Se non lo è, le tue modifiche restano dove sono, come prima.

**Il principio dietro**: la tua config e quella di Arturo convivono senza che tu debba pensarci.
Le tue modifiche restano tue, gli aggiornamenti cambiano solo i file di Arturo.

**A chi serve**: a chi ha già cambiato un comando di Arturo. Gli altri non vedono differenze.

---

## 2026-10-15 — Un solo modo di leggere gli heredoc per tutte le guardie

**Cosa cambia**: quattro guardie leggevano gli heredoc ognuna a modo suo, e sbagliavano in punti
diversi. Una here-string (`<<<"x"`) faceva sparire il resto del comando: una lettura di
`~/.ssh` scritta dopo passava senza conferma. Il testo mandato a bash con `cat <<'EOF' | bash`
sfuggiva a due guardie su quattro. Ora le quattro usano lo stesso modulo, `hooks/heredoc.py`.

**Il principio dietro**: il testo che una guardia toglie è testo che non controlla. Quattro copie
della stessa regola divergono, e il buco sta sempre nella copia che nessuno ha guardato.

**A chi serve**: a tutti, senza fare niente: arriva col prossimo `/aggiorna`.

---

## 2026-10-15 — Guardie che leggono il comando come lo esegue la shell

**Cosa cambia**: un invio di email o messaggi da terminale ora chiede conferma invece di essere
bloccato: vedi il comando vero e decidi tu. Le guardie leggono il comando come lo esegue la shell:
il testo di un heredoc scritto su file, un messaggio di commit e il pattern di `grep` non fanno più
scattare allarmi, mentre un `rm` col percorso completo o dentro `sh -c` si vede. Un git hook o un
servizio che parte all'accesso (`~/Library/LaunchAgents` su Mac, `~/.config/systemd/user` e
`~/.config/autostart` su Linux) si scrive solo con la tua conferma. Le reti locali contano tutte
come interne (anche `172.16.x`-`172.31.x` e le IPv6 locali); un servizio esterno che usi con la tua
chiave lo scrivi in `hooks/api-fidate.local`. Salvare un handoff o una memoria non chiede più
conferma; settings, hook e file di sblocco la chiedono sempre. La statusline mostra il ramo git, un
`*` se ci sono modifiche e la quota dell'abbonamento. Dopo ogni modifica a un file TypeScript o Vue
Claude vede subito gli errori di tipo. Creare una bozza via un collegamento non chiede conferma,
inviarla sì.

**Il principio dietro**: un blocco che sbaglia insegna a Claude ad aggirare la guardia, una
conferma mostra a te il comando vero. Queste correzioni girano da settimane nella config
dell'autore.

**Da sapere**: all'avvio Arturo prova le sue guardie in background, al massimo ogni 12 ore, senza
rallentare la sessione. Se una guardia non funziona su questo computer, la sessione dopo una riga
`GUARDIE` te lo dice. Li spegni con `ARTURO_BANCHI_AVVIO=0`. Se il tuo `CLAUDE.md` supera le 200
righe, Claude ti avvisa quando lo modifica (il limite si cambia con `ARTURO_CLAUDE_MD_RIGHE`).

## 2026-10-15 — Gate che non mentono, lavori lunghi, lettura del web senza browser

**Cosa cambia**: il gate di `/fine` è uno script (`bin/validation-gate-lang.sh`). Riconosce se il
progetto è Node, Python o testo, e lancia i controlli giusti. Prima il gate leggeva l'esito dei test
in un modo che, nella shell di Claude Code, poteva restare vuoto e sembrare un verde. Un comando lungo
ha una strada sua, `bin/bgjob.sh`: gira staccato dalla sessione e scrive l'esito su un file.
`/system-audit` segnala anche i comandi citati nei documenti che non esistono più, e i plugin
installati ma spenti. In `/setup` c'è una fase facoltativa per `scrape`, che legge una pagina web e
tiene solo il testo utile.

**Il principio dietro**: un controllo vale solo se sa dire "rosso". Ogni gate nuovo ha un caso
avvelenato, una versione rotta apposta che deve bocciare. Il "non so" è un esito onesto: il testo e
gli strumenti mancanti danno "inconclusivo", mai verde.

**Da sapere**: `scrape` occupa circa 300 MB e si installa solo se dici sì in `/setup`. Non finge di
essere un browser: se un sito blocca i programmi, te lo dice e ti consiglia di aprire la pagina nel
browser. La pulizia mensile (`bin/monthly-cleanup.sh`) è facoltativa: prova prima con `--prova`.

## 2026-10-15 — /inizio e /fine: il contesto in una chiamata, un handoff che regge

**Cosa cambia**: `/inizio` raccoglie il contesto del progetto in una chiamata sola
(`arturo contesto`): cosa è cambiato in git, la ripartenza degli ultimi handoff, i todo aperti
divisi fra te e Claude, le scadenze dei prossimi giorni e il todo da cui ripartire. Con
`/inizio --tutti` aggiorna anche tutti i progetti della tua cartella dei progetti. `/fine` parte
dall'inventario dei file che la sessione ha scritto, anche fuori dal progetto (Download, Scrivania,
cartelle temporanee), e propone dove deve finire ognuno. Prima di chiudere controlla l'handoff: la
tabella dei pendenti c'è sempre, ogni riga è un todo vero dell'archivio, e chi agisce è tu, decidi
o io. Tiene gli ultimi 5 handoff per progetto, ma prima ti mostra cosa conteneva quello che esce, e
rigenera l'indice dei progetti.

**Il principio dietro**: una sessione nuova vale quanto quello che trova. Un handoff che dice "cosa
resta" senza dire cosa, o un file lasciato in una cartella che sparisce al riavvio, è lavoro perso.
Meglio un controllo che ferma la chiusura che una ripartenza al buio.

**Da sapere**: gli handoff restano solo sul tuo computer, come prima, e viaggiano fra le tue
macchine solo se la config ha un remote privato. I file che l'inventario trova fuori da un progetto
non si spostano da soli: Claude ti chiede dove li tieni. Da terminale il contesto lo vedi con
`python3 ~/.claude/bin/arturo contesto <progetto>`.

## 2026-10-15 — /apri, avvisi sotto il prompt, esempi per lo strato

**Cosa cambia**: scrivi `/apri` e si apre l'ultimo link o file che Claude ha citato, con il
programma predefinito del tuo computer. Sotto il prompt, oltre alla cache fredda, compaiono due
avvisi nuovi: i banchi delle guardie sono rossi, oppure un account Google della CLI `gws` va
ricollegato. Se usi `gws`, un errore di credenziali ora si dichiara al primo colpo, con il comando
per rifare il login. La skill dell'italiano semplificato ha un catalogo dei tic della scrittura
generata. Chi cura lo strato di un'organizzazione trova in `esempi/` tre modelli da adattare: le
email che imparano dalle correzioni, il recap delle riunioni dalla trascrizione intera, l'anteprima
prima dell'invio. Per il design delle interfacce, `docs/impeccable.md` spiega come installare
Impeccable dall'autore.

**Il principio dietro**: un avviso compare solo quando c'è qualcosa da fare. Una cosa che esiste già
fatta bene altrove si installa da lì, non si copia.

**Da sapere**: gli esempi dello strato non sono attivi finché il referente non li copia nello
strato. L'avviso dei banchi compare solo se un banco è rosso: i banchi partono da soli
all'avvio, al massimo ogni 12 ore, e il rimedio è lo stesso della riga `GUARDIE`. L'avviso di `gws`
tace se non usi `gws`. Per spegnere un mod: `/plugin`, poi il mod, poi disattiva.

## 2026-10-15 — Una memoria che puoi accendere

**Cosa cambia**: Claude Code salva da solo alcune note sulle sessioni passate: cosa preferisci,
cosa hai deciso, dove stanno le cose. Ora Arturo può usarle in ogni progetto. Se accendi la
memoria, a ogni messaggio Arturo cerca le note che parlano della stessa cosa e dice a Claude dove
sono. Claude le apre solo se servono. Ogni nota e ogni handoff che Claude scrive passa da un
controllo, anche a memoria spenta: se dentro c'è una password o un'istruzione nascosta, Claude riceve un avviso. Con
`arturo memoria cerca "parole"` cerchi a mano, con `arturo memoria controlla` trovi le note senza
descrizione e i link rotti. Puoi aggiungere una tua cartella di note con
`arturo memoria cartella aggiungi <cartella>`.

**Il principio dietro**: una memoria serve se la trovi quando ti serve, e se non porta dentro
niente che non hai scritto tu. Le note restano tue e restano qui: nessun server, nessun archivio
nuovo, niente nella telemetria.

**Da sapere**: la memoria è spenta. Si accende in `/setup` oppure con
`python3 ~/.claude/bin/arturo memoria accendi`, e si spegne con `arturo memoria spegni`. Spegnerla
non cancella nessuna nota. `arturo memoria` da solo ti dice se è accesa e quante note vede.

## 2026-10-15 — La telemetria si allarga, e serve a correggere Arturo ogni settimana

**Cosa cambia**: la telemetria di Arturo manda qualche evento in più, sempre senza contenuti. Partono
la fase di `/setup` a cui arrivi, il nome di una guardia che ti chiede conferma e se poi hai detto sì,
una guardia che si rompe, un `/aggiorna` rifiutato, annullato o scartato, la versione di Claude Code,
e del percorso a tappe i soli numeri: la tappa, quante decisioni e limiti hai tenuto, quante proposte
di delega e quanti no. Mai cosa hai scritto. Alla prima sessione dopo l'aggiornamento Claude ti dice
di nuovo cosa esce, perché la promessa è cambiata. L'elenco intero è nell'Impegno 3 del README.

**Il principio dietro**: chi comincia spesso non sa dire dove si blocca. Ogni lunedì chi mantiene
Arturo legge dove le persone si fermano: una fase di `/setup` abbandonata, una guardia che chiede e
riceve sempre sì (una domanda inutile insegna a rispondere sì senza leggere), un aggiornamento che
nessuno vuole, una tappa dove si resta fermi. Da lì nascono le correzioni, e ognuna lo dirà nella sua
voce di questo file. Sono numeri, non verdetti: il giudizio resta a una persona.

**Da sapere**: la spegni quando vuoi con `python3 ~/.claude/bin/arturo telemetria spegni`, e
`python3 ~/.claude/bin/arturo telemetria mostra` ti fa vedere esattamente cosa parte. L'id che parte
con gli eventi è casuale ma resta lo stesso: per questo non li chiamiamo anonimi.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-15 — Scegli come ti scrive Claude

**Cosa cambia**: Arturo porta due stili di scrittura. **Guida**, lo stile di partenza, scrive frasi
semplici, senza gergo, e dice prima l'esito e poi cosa devi fare tu. **Conciso** è per chi usa Claude
ogni giorno e vuole leggere poco. `/setup` ha una fase nuova per scegliere fra questi due e i tre
di Claude Code (Default, Explanatory, Learning). Lo cambi quando vuoi con `/output-style`.

**Il principio dietro**: lo stile standard di Claude Code è scritto per chi sviluppa software. Chi
usa Claude per scrivere, cercare e ordinare il lavoro merita risposte pensate per lui.

**Da sapere**: dopo questo aggiornamento le risposte arrivano nello stile Guida, dalla sessione
successiva. Lo stile cambia solo la scrittura: permessi e guardie restano gli stessi. Se vuoi uno
stile tuo, crealo in `~/.claude/output-styles/` con un nome nuovo: nessun aggiornamento lo tocca.

## 2026-10-15 — Guardie più strette dove servono, meno allarmi dove non servono

**Cosa cambia**: Claude chiede conferma prima di leggere una password con `bw get`, di aprire un
file `.env`, di rispondere, inoltrare o condividere via un collegamento (Gmail, Calendar, Drive,
GitHub) e di correggere un commit con `--amend`. Non può più eseguire codice arbitrario nel browser
né lanciare un altro Claude senza permessi. Il controllo dei segreti nei commit parte anche con le
forme che prima lo saltavano (`env … git commit`, un commit a capo, `git --no-pager commit`). Un
indirizzo `.ts.net` non conta più come interno: se lavori con la tua tailnet, scrivi i tuoi host in
`hooks/hosts-interni.local`. Due falsi allarmi spariscono: `sed` in lettura seguito da un ciclo
`for w`, e `rsync --delete` in prova (`-n`) o citato in un testo. La statusline torna a mostrare il
task in corso, e il suono parte solo quando Claude aspetta te.

**Il principio dietro**: una guardia vale se ferma il danno vero e tace sul lavoro normale. Queste
correzioni arrivano dalla config dell'autore, dove giravano da settimane.

**Da sapere**: se usavi `bw get` senza conferma, ora Claude te la chiede ogni volta. È voluto: la
password finirebbe nella conversazione. Gli allow larghi (`python3`, `curl`, `docker`, `brew`)
escono: nella modalità auto decide il controllo di sicurezza di Claude Code, che ora riceve
istruzioni chiare su cosa è lavoro normale (script di prova, pulizia dei rami già uniti, commit nei
tuoi repository). I comandi di sola lettura (`ls`, `cat`, `git status`…) restano liberi.

## 2026-10-14 — Arturo convive con la tua config

**Cosa cambia**: le tue aggiunte a un comando di Arturo hanno un posto loro,
`~/.claude/personale/<comando>.md`. Quando lanci il comando Claude le legge, e nessun aggiornamento
le tocca. Se hai già modificato un comando di Arturo, `/aggiorna personale` sposta le tue modifiche
lì e riporta il comando com'era: l'aggiornamento successivo non va più in conflitto. All'avvio una
riga `DERIVA` ti avvisa quando la distanza da Arturo rischia di rompere qualcosa: un comando
modificato, un hook di Arturo tolto o spento. Il promemoria del brief non scatta più sui comandi e
sulle richieste chiare e piccole: solo su un lavoro che tocca più file, ha effetti fuori dal
computer o si può capire in due modi.

**Il principio dietro**: Arturo accompagna la tua config, non la sostituisce, e non deve intralciare
l'uso naturale dell'LLM. Dove le due config si toccano serve un confine chiaro: il tuo da una parte,
quello di Arturo dall'altra.

**Da sapere**: la telemetria ha due eventi nuovi, `deriva` e `config`. Dei file esce solo la
posizione dentro Arturo, che è pubblica: mai i tuoi file né i percorsi del tuo computer. Una config
rotta parte subito, perché spegne le guardie. La spegni come sempre con
`python3 ~/.claude/bin/arturo telemetria spegni`.

## 2026-10-14 — Prima di cancellare vedi cosa sparisce, e zsh si comporta come bash

**Cosa cambia**: un mod nuovo, `blast-radius`. Quando Claude sta per lanciare `rm -rf`, `git reset
--hard`, `git clean` o un push forzato, il comando si ferma e compare un pannello: quanti file
spariscono e quali, quali modifiche non salvate si perdono, quali commit. Premi Procedi o Annulla.
`riscrivi-bash` fa comportare zsh, la shell del Mac, come bash: un glob che non trova file
(`ls *.png` in una cartella senza png) non ferma più il comando con "no matches found". Escono due
mod che nessuno usava: `menu-contesto` e `agent-flow`.

**Il principio dietro**: prima di un gesto che non si annulla, devi vedere cosa fa, non leggere
un comando. E una comodità che nessuno apre è solo codice da mantenere.

**Da sapere**: niente da fare. Se `blast-radius` ti ferma troppo spesso, spegnilo con `/plugin`.


## 2026-10-14 — Una striscia per i conti, e il controllo degli invii guarda cosa gira davvero

**Cosa cambia**: sotto la frase che riassume i tuoi todo, la pagina di `arturo web` ha una
striscia. Ogni pezzo è largo quanto la sua parte: quelli che toccano a te, quelli da decidere,
quelli in mano a Claude, quelli fermi. A colpo d'occhio vedi dove pesa il lavoro. Il controllo
degli invii email ora giudica il comando che gira, non le parole che contiene: cercare "smtplib"
in una cartella o scriverlo in una nota non si ferma più. Si fermano invece forme che prima
passavano: `find -exec sendmail`, `awk` con `system()`, `git send-email`, un testo mandato a `sh`.

**Il principio dietro**: una guardia che blocca la prosa insegna ad aggirarla. Una guardia che
lascia passare un invio travestito non protegge. Si giudica il codice eseguito.

**Da sapere**: niente da fare. Se hai uno script tuo che usa `git send-email`, ora Claude ti chiede
conferma prima di lanciarlo.

## 2026-10-13 — Meno dati in uscita, copie di prova che non si perdono, guardie più precise

**Cosa cambia**: quattro correzioni. La telemetria manda il nome di un comando solo se il comando è
di Arturo: un comando che hai scritto tu in `~/.claude/commands/` ha un nome tuo, e da oggi non parte.
Se un aggiornamento o il sync fra le tue macchine si è fermato su un conflitto, la copia di prova
con il conflitto resta finché non la concludi o dici di scartarla: prima un `/aggiorna` successivo la
toglieva in silenzio, con il lavoro che c'era dentro. All'avvio della sessione Arturo te la ricorda.
`/segnala` torna al canale diretto anche se con la prima versione avevi usato la email o il web.
`/strato` funziona dal secondo passo in poi, e `pubblica` non manda niente se un controllo fallisce.

**Il principio dietro**: una promessa vale per quello che il codice fa, non per quello che il README
dice. La telemetria prometteva "il nome di un comando di Arturo", e mandava il nome di qualunque
comando. Lo stesso vale per le guardie: un invio verso fuori non deve passare solo perché nello
stesso comando compare anche un indirizzo interno.

**Da sapere**: scrivere un `CLAUDE.md` da terminale (`>`, `sed -i`, `cp`) ora chiede conferma, come
già succedeva modificandolo con Claude. Leggerlo o copiarlo altrove no. Il controllo delle emoji
guarda solo il testo che Claude ha appena scritto: le emoji che avevi già messo in un file restano.

## 2026-10-13 — Telemetria minima, e /segnala arriva da sola

**Cosa cambia**: Arturo comincia a mandare a chi lo mantiene pochi dati d'uso anonimi. Sono
sempre gli stessi: l'avvio di una sessione, il nome dei comandi di Arturo che usi, il nome della
guardia che ti ha fermato, l'esito di `/aggiorna` e il tipo delle segnalazioni. Partono con un id
casuale, la versione e il sistema operativo, con il giorno e mai l'ora. È accesa di default.
In più `/segnala` non ti chiede più di mandare una email a mano. Dopo il tuo sì, la segnalazione
arriva direttamente a chi mantiene Arturo. Se la rete non risponde, parte da sola alla sessione dopo.

**Il principio dietro**: questo cambia una promessa. Fino a oggi l'Impegno 3 del README diceva
"Niente telemetria", e la novità di stamattina diceva che `/segnala` non era telemetria. Chi
mantiene Arturo ha deciso di cambiarla, perché senza dati d'uso non vede dove le persone si
bloccano. Le persone per cui Arturo è fatto spesso non lo sanno dire, e di sicuro non aprono una
issue. Il nuovo Impegno 3 dice cosa parte, cosa non parte mai e come spegnerla.

**Da sapere**: non partono mai prompt, file, percorsi, nomi, risposte o il tuo percorso a tappe.
Il server è open source (`server/`) e non salva il tuo indirizzo IP. Vedi cosa parte con
`python3 ~/.claude/bin/arturo telemetria mostra` e la spegni con
`python3 ~/.claude/bin/arturo telemetria spegni` oppure con `DO_NOT_TRACK=1`. Alla prima
sessione dopo l'aggiornamento Claude te lo dice una volta. Per far cancellare i tuoi dati scrivi
a federico@stellakamikaze.org con il tuo id.

## 2026-10-13 — Dire ad Arturo cosa non va, con /segnala

**Cosa cambia**: c'è un comando nuovo, `/segnala`. Lo usi quando qualcosa di Arturo non funziona,
quando hai un'idea o quando vorresti collegare uno strumento che usi nel lavoro. Claude scrive il
testo con te, toglie nomi, clienti e segreti, e te lo fa leggere. Parte solo con il tuo sì: come
issue su GitHub se hai un account, altrimenti come email a chi mantiene Arturo. Arturo poi te lo
propone da solo: subito dopo un intoppo, con il testo già pronto, e a fine sessione con una
domanda breve, al massimo una volta a settimana.

**Il principio dietro**: Arturo migliora con quello che gli dicono le persone che lo usano.
Una cosa che ti ha fatto perdere tempo, raccontata in tre righe, diventa una correzione per tutti.

**Da sapere**: non è telemetria. Niente parte senza che tu abbia visto il testo e detto sì. La
issue su GitHub è pubblica, la email arriva solo a chi mantiene Arturo. Una copia di ogni
segnalazione resta sul tuo computer, in `~/.claude/data/segnalazioni/`. Se non vuoi gli inviti:
`python3 ~/.claude/bin/arturo segnala basta`. `/segnala` resta lì quando ti serve.

## 2026-10-12 — Anche il sync fra le tue macchine passa dalla copia di prova

**Cosa cambia**: se hai un tuo repository, `/inizio` scarica le modifiche delle tue altre macchine
come fa ora `/aggiorna`: le prova in una copia a parte e le porta dentro solo se la config resta
integra. Se due macchine hanno cambiato le stesse righe, i tuoi file restano com'erano e il
conflitto aspetta nella copia di prova. Claude te lo mostra e lo risolvete insieme.

**Il principio dietro**: lo stesso di `/aggiorna`. I file che Claude Code sta usando cambiano solo
quando il risultato è già controllato.

**Da sapere**: il sync fra le tue macchine non finisce nel registro di `/aggiorna indietro`, che
torna indietro solo sugli aggiornamenti di Arturo.

## 2026-10-12 — Aggiornare senza mai rompere i file in uso

**Cosa cambia**: `/aggiorna` non unisce più l'aggiornamento dentro `~/.claude`. Lo prova in una copia
a parte, controlla lì la config, e porta dentro solo un risultato integro. Se le tue modifiche e
quelle di Arturo vanno in conflitto, i tuoi file restano com'erano, senza segni di conflitto:
Claude ti mostra il conflitto nella copia di prova, lo risolvete insieme lì e poi lo porta dentro.
In più la procedura che applica l'aggiornamento arriva con l'aggiornamento stesso: una correzione
alla procedura vale già dal primo giro. Prima, un conflitto poteva lasciare i segni dentro
`settings.json` e negli hook, e Claude Code spegneva le guardie senza dirlo.

**Il principio dietro**: i file che Claude Code sta usando cambiano solo quando il risultato è già
controllato.

**Da sapere**: questo aggiornamento lo applica ancora la procedura che hai installato. La copia di
prova vale dal giro successivo. Se `/aggiorna` ti dice che la config è già rotta, c'è un merge o un
pull rimasto a metà da prima: sistemalo con Claude prima di aggiornare.

## 2026-10-09 — Aggiornare con modifiche non salvate: si ferma e te lo dice

**Cosa cambia**: se hai cambiato un file della config senza salvarlo con un commit (lo fa anche
`/setup` in `settings.json`), `/aggiorna` non applica niente e `/inizio` non scarica dal tuo
repository. Ti dicono quali file sono e cosa fare: li salva `/fine`, poi riprovi. Prima
l'aggiornamento poteva lasciare `settings.json` con i segni di un conflitto e le guardie spente,
dicendo che era tutto a posto. Ora il messaggio "ho riportato la copia a prima" compare solo se è
vero. In più `/aggiorna` mostra le guardie e prende gli aggiornamenti da `upstream` anche quando
hai un tuo repository.

**Il principio dietro**: un comando che fallisce lo dice, e non dice mai "fatto" senza controllare.

## 2026-10-09 — Cinque mod nuovi: segreti, Bash, menu, cache, agenti

**Cosa cambia**: in `skills/` arrivano cinque mod che Claude Code carica da solo.
- `redazione-segreti`: se nell'output di un tool c'è una chiave, un token o la password di un database,
  Claude vede solo la sua forma (tipo, lunghezza, prime cifre dell'hash). Il valore resta sul tuo computer.
- `riscrivi-bash`: due comandi che sul Mac fallivano sempre ora vengono corretti prima di partire.
- `menu-contesto`: quando Claude ti propone un menu, il testo che lo precede si legge in un pannello.
- `cache-fredda`: sotto il prompt compare un avviso quando la cache è scaduta e il prossimo messaggio
  costerebbe come rileggere tutta la conversazione. È il momento giusto per chiedersi se serve una
  sessione nuova.
- `agent-flow` (`/agent-flow`): un pannello con l'albero degli agenti al lavoro, per capire come
  Claude divide un compito, cosa passa a ognuno e cosa torna indietro. Viene da un altro autore: è una
  copia fissata, letta riga per riga, che non si aggiorna da sola.

**Il principio dietro**: sono i mod che chi sviluppa Arturo usa ogni giorno, tolti i riferimenti
personali. I segreti non entrano più nella conversazione invece di essere segnalati dopo. Gli avvisi
arrivano solo quando c'è qualcosa da fare.

**A chi serve**: a tutti, senza fare niente. Per spegnerne uno: `/plugin`.

---

## 2026-10-04 — Il tavolo dei progetti

**Cosa cambia**: la pagina delle cose da fare (`arturo web`) ora parte dai progetti. In cima trovi
"Da dove partirei": un todo solo, scelto con una regola fissa, e il motivo in parole ("Sblocca #7",
"Scade domani"). Sotto, un foglio per ogni progetto, con il prossimo passo, gli altri todo in vista,
chi agisce e la scadenza più vicina. Davanti stanno i progetti dove qualcosa chiede te, dietro quelli
tutti in mano a Claude. Un foglio si apre e diventa la pagina del progetto. Lì un todo si apre nel
dettaglio, con le note datate, la storia di ogni passaggio e quello che aspetta o sblocca. In testa
c'è anche una riga con la tappa del tuo percorso.

**Il principio dietro**: il modo in cui chi sviluppa Arturo riparte ogni mattina. Prima la cosa da
cui partire, poi i progetti uno per uno, ogni todo con il segno di chi agisce. La regola di "Da dove
partirei" è la stessa per ogni vista: prima quello che chiede una persona, poi quello che sblocca
altri todo, poi scadenze e priorità.

**A chi serve**: a chi ha più di un progetto aperto e vuole vedere da dove ripartire senza leggere
l'elenco intero.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-04 — Claude ti dice quale skill usa

**Cosa cambia**: nel brief che Claude mostra prima di ogni lavoro c'è una riga nuova, "Skill:".
Dice quale skill userà e perché, oppure "nessuna". Se una skill che non hai nominato fa meglio il
lavoro, te lo dice lì. Il brief si carica anche più leggero: la parte per scrivere prompt destinati
ad altri strumenti (ChatGPT, Midjourney e simili) ora si legge solo quando la chiedi. In `/setup`
ci sono due regole consigliate in più per il tuo `CLAUDE.md`: l'ultima riga di ogni lavoro dice il
prossimo passo, e un risultato visivo è "fatto" solo quando Claude l'ha aperto come lo vedrai tu.

**Il principio dietro**: l'harness si misura su come lo usi. Le due regole e la riga Skill vengono
dall'analisi di due mesi d'uso reale di chi sviluppa Arturo: "e adesso?" chiesto 59 volte, il
"fatto" non verificato come correzione più frequente sui lavori visivi.

**A chi serve**: a chi non sa ancora quali skill ha, e a chi vuole capire dal brief se Claude ha
preso la strada giusta prima che cominci.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

---

## 2026-10-03 — Il percorso a tappe

**Cosa cambia**: chiedi a Claude "a che punto sono?" oppure scrivi `/percorso`. Vedi la tua
tappa fra quattro: Osserva, Prova, Delega, Orchestra. Accanto a ogni tappa c'è il numero del todo
che la prova, così puoi controllare. Vedi anche la lista "Cose che tieni per te" e un esercizio
della settimana sul tuo lavoro vero. `/inizio` ti mostra la tappa in una riga. A fine sessione
`/fine` può proporti una sola delega, e dopo un tuo no tace per qualche giorno.

**Il principio dietro**: automatizza la forma, frena l'impegno. Il percorso conta le decisioni
che tieni, non il lavoro che deleghi. Le tappe si aprono con una decisione presa prima che Claude
lavori, un limite che dichiari o un no motivato. Delega chiede due segni insieme: una decisione
presa prima che Claude lavori (con `deciso`, o chiudendo tu un todo DECIDI TU) e un limite (un
perché detto da te su un todo tuo, oppure un no motivato). Il nuovo capitolo "Tieni la decisione" lo
racconta (`docs/principi/05-tieni-la-decisione.md`), e `docs/esercizi.md` ha otto esercizi.

**Da sapere**: il percorso si calcola solo sul tuo computer, dai tuoi todo, e il suo stato resta lì.
I todo da cui nasce (i perché e le note "Tenuto:") viaggiano come gli altri todo: solo verso il
tuo repository privato, con `/fine`. Il referente della tua organizzazione non vede il percorso. Dopo un no alla proposta di `/fine`, Claude tace
tre giorni. Dopo due no di fila, due settimane. "Basta suggerimenti" le spegne finché non dici
"riprendi i suggerimenti". Pausa e silenzi valgono solo sul computer dove li dici: lo stato del
percorso non viaggia con `/fine`.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — Il pannello delle cose da fare

**Cosa cambia**: scrivi `/dafare` e dentro Claude Code si apre un pannello con le tue cose da
fare, divise in TOCCA A TE, DECIDI TU, FACCIO IO e FERMO. Ogni riga dice il progetto e la
scadenza. Scegli una riga con il numero e premi una lettera: `f` fatto, `s` ferma, `r` riprendi,
`c` chi lo fa, `a` avvicina, `l` allontana. `p` mostra un progetto alla volta. Quando hai cose
aperte, sopra il prompt compare una riga sottile: "3 cose da fare · /dafare per vederle".

**Il principio dietro**: vedere in ogni momento cosa è in mano tua e cosa in mano a Claude, e
agire senza scrivere comandi. Il pannello non ha un archivio suo: scrive con la stessa CLI
`arturo todo` che usa Claude, quindi le due viste dicono sempre la stessa cosa.

**Da sapere**: Esc chiude il pannello, `u` annulla l'ultimo tasto. Se i tasti non rispondono
più, premi ctrl+x tab oppure riscrivi `/dafare`. `/dafare nascondi` spegne la riga sopra il
prompt, `/dafare mostra` la riaccende. Il pannello chiede Claude Code 2.1.287 o successivo:
`/setup` controlla la versione. Arriva con l'aggiornamento e c'è dopo la riapertura di Claude
Code.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — La pagina delle cose da fare

**Cosa cambia**: ora vedi i tuoi todo anche in una pagina del browser. Chiedi a Claude "fammi
vedere le mie cose da fare in una pagina", oppure scrivi nel terminale
`python3 ~/.claude/bin/arturo web` (solo `arturo web` se con `/setup` hai aggiunto il comando breve). Da lì aggiungi un todo, lo segni fatto, lo modifichi o lo
fermi. Su un todo di "Decidi tu, poi faccio io" premi "Ho deciso", scrivi la scelta e il lavoro
passa a Claude. Dopo ogni azione compare "Annulla", salvo dopo una nota. Niente si
cancella dall'archivio.

**Il principio dietro**: lo stesso archivio, più modi di guardarlo. La pagina non tiene dati suoi
e segue le stesse regole di `arturo todo`: quello che fai nella pagina lo vede Claude, e quello
che scrive Claude compare nella pagina entro 20 secondi.

**Da sapere**: la pagina è facoltativa e gira solo sul tuo computer. Il link contiene una chiave
che cambia a ogni avvio, e la pagina non si collega a internet. Si spegne da sola dopo 30 minuti
senza la pagina aperta, oppure con il bottone "Spegni la pagina".

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-10-03 — Le tue cose da fare, in un posto solo

**Cosa cambia**: quando dici a Claude "ricordami di mandare il preventivo venerdì", il todo
finisce in un archivio sul tuo computer e ci resta. Prima i task sparivano a fine sessione, e
sopravviveva solo la tabella dell'handoff. Ogni todo sa di quale progetto è, quando scade e chi
agisce: tu, tu che decidi e poi Claude, oppure Claude. `/fine` ci scrive quello che resta da
fare, `/inizio` te lo mostra diviso in TOCCA A TE, DECIDI TU, FACCIO IO e FERMO. Dal terminale
lo leggi con `python3 ~/.claude/bin/arturo todo` (con `/setup` puoi aggiungere il comando breve
`arturo todo`). Quando hai deciso su un todo di DECIDI TU, dillo a Claude, oppure scrivi
`python3 ~/.claude/bin/arturo todo deciso 4 "piano B"`: la scelta resta nel todo e il lavoro passa
a Claude.

**Il principio dietro**: delegare vuol dire anche sapere sempre cosa è in mano tua e cosa in
mano a Claude. Un elenco unico, con chi agisce scritto accanto a ogni cosa, rende visibile
questa divisione. È la base delle prossime viste: un pannello dentro Claude Code e una pagina web.

**Da sapere**: i todo stanno in `~/.claude/data/todo/` e nessun aggiornamento li tocca. Viaggiano
tra i tuoi computer solo se il repository della tua config è privato.

<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->

## 2026-09-30 — Lo strato della tua organizzazione

**Cosa cambia**: se lavori in un'organizzazione, Arturo ora può diventare "vostro". Il
**referente**, una persona del team, prepara con `/strato crea` uno strato con chi siete, come
scrivete, i lavori che si ripetono e i dati che non devono uscire. I colleghi lo ricevono con
`/strato installa` e lo tengono aggiornato con `/aggiorna`. All'avvio Claude sa per chi lavora, la
voce dell'organizzazione è una skill, e prima di mandare fuori un dato riservato chiede conferma.

**Il principio dietro**: uno strumento entra in un'organizzazione quando qualcuno del team lo
adatta al lavoro vero, non quando ognuno lo configura da solo. Lo strato vive nel repository
privato dell'organizzazione, separato da Arturo: gli aggiornamenti dei due non si pestano i piedi.

**Da sapere**: la guida del ruolo è in `docs/referente.md`. Lo strato è un plugin di Claude
Code: dopo l'installazione va riaperto Claude Code.

## 2026-09-30 — Aggiornamenti che non rompono niente, cartelle protette

**Cosa cambia**: tre cose che senti subito.

1. **Cancellare una cartella chiede sempre conferma.** Prima Arturo proteggeva solo la
   sua configurazione e la cartella dei progetti: una cartella di capitoli, la Scrivania
   o i Documenti si potevano cancellare senza domande. Ora ogni cancellazione di una
   cartella intera ti chiede il sì, tranne le cartelle che un programma ricrea da solo
   (per esempio `node_modules` o `dist`) e i file temporanei.
2. **Solo `/aggiorna` applica gli aggiornamenti.** `/inizio` e l'avvio li controllano e
   basta. `/aggiorna` ti dice quale versione hai e quale arriva, ti racconta cosa cambia
   nelle guardie, e se qualcosa va storto annulla da solo: la tua copia non resta mai a
   metà. `/aggiorna indietro` funziona anche dopo un `/fine`, e un secondo
   `/aggiorna indietro` torna ancora più indietro.
3. **Auto mode.** Claude Code ora giudica ogni comando con il suo classificatore, e le
   guardie di Arturo restano sopra di lui. Meno domande su lavoro normale, le stesse
   domande sulle azioni che non si annullano.

Anche: `/debug` ora si chiama `/diagnosi`, per non nascondere il `/debug` di Claude
Code. `/progetto` ha un ramo per chi non scrive codice (un libro, una ricerca, un
corso). Le emoji nei tuoi testi restano: il controllo vale solo per il codice.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer.
Per questo passa da una porta sola, dopo il tuo sì, e deve poter tornare indietro
sempre. Un `settings.json` rotto spegne tutte le guardie senza dire niente: Arturo ora
lo controlla all'avvio, prima e dopo ogni aggiornamento, e prima di ogni `/fine`.

**Da sapere**: dopo questo aggiornamento chiudi e riapri Claude Code. Se all'avvio vedi
una riga `CONFIG ROTTA`, fermati e chiedi a Claude di sistemarla prima di lavorare. Su
Windows Arturo funziona solo dentro Git Bash: `/setup` ora lo controlla.

## 2026-09-16 — Dove segnalare un problema

**Cosa cambia**: segnalare un problema ora ha una strada guidata. Quando apri una
issue su GitHub trovi due moduli pronti: "Qualcosa non funziona" (cosa stavi
facendo, cosa ti aspettavi, cosa è successo) e "Una proposta" (quale problema
vuoi risolvere). Nessuna domanda tecnica obbligatoria. Se invece trovi un
segreto esposto o un modo per aggirare una guardia, il modulo te lo dice subito:
non aprire una issue pubblica, usa la procedura privata in `SECURITY.md`, col
pulsante "Report a vulnerability" nella scheda Security del repository.

**Il principio dietro**: una segnalazione di sicurezza pubblica avvisa anche chi
potrebbe approfittarne. Il canale privato protegge tutti gli utenti mentre il
problema viene chiuso. Il resto delle segnalazioni resta pubblico e semplice:
chi apre una issue può non essere tecnico, quindi i moduli chiedono fatti, non
diagnosi. Tutto questo senza toccare l'impegno sulla telemetria: Arturo non
aggiunge contatori; chi mantiene misura l'uso solo dai dati pubblici di GitHub,
come scritto in `docs/manutenzione.md`.

**Da sapere**: se in passato hai aperto una issue per un falso positivo di una
guardia, quella strada non cambia: resta una issue normale, col comando esatto.
In privato va solo ciò che non deve diventare pubblico.

## 2026-09-16 — I tuoi file restano tuoi

**Cosa cambia**: ora c'è un confine chiaro tra i file di Arturo e i file tuoi. Il tuo
`CLAUDE.md` e i tuoi host fidati non vivono più dentro i file che gli aggiornamenti
sostituiscono. Gli host personali si scrivono in `hooks/hosts-interni.local`, una voce per
riga (hostname o rete): le due guardie anti-esfiltrazione lo leggono e non chiedono più
conferma verso quei server. `/setup` (FASE 6) guida su quel file invece di modificare i
`.py`, e il README ha una tabella che dice cosa arriva con gli aggiornamenti e cosa resta
tuo.

**Il principio dietro**: una personalizzazione scritta dentro un file di Arturo è una
modifica che il prossimo aggiornamento può travolgere o mandare in conflitto. Spostandola
in un file tuo, ignorato da git, l'aggiornamento non la tocca più. Il file sta dentro
`hooks/` di proposito: le guardie esistenti proteggono ogni scrittura lì sotto, quindi un
prompt malevolo non può aggiungere un host fidato senza la tua conferma.

**Da sapere**: se in passato hai aggiunto un host dentro `exfil-guard.py` o
`web-egress-guard.py`, al prossimo `/aggiorna` quella modifica può entrare in conflitto:
sposta la riga in `hooks/hosts-interni.local` e accetta la versione nuova dei due file.

## 2026-09-16 — Tornare indietro dopo un aggiornamento

**Cosa cambia**: `/aggiorna indietro` riporta la tua copia alla versione di prima dell'ultimo
aggiornamento. Prima di toccare qualunque cosa ti mostra in parole semplici cosa torna indietro: i
commit arrivati e le novità che spariranno. Lo fa solo dopo il tuo sì. In più, l'avviso di
avvio "la config è AVANTI di N commit" non compare più se il tuo `origin` è il repo originale di
Arturo: su quel repo non puoi scrivere, quindi i commit locali sono normali e l'avviso era solo
rumore. Se `origin` è un repo tuo, l'avviso resta.

**Il principio dietro**: un aggiornamento è codice di altri che gira sul tuo computer (vedi
"Cosa non è neutro"): la scelta è tua solo se puoi anche tornare indietro. E un avviso che non
puoi risolvere, come "non hai pushato" su un repo dove non puoi pushare, insegna a ignorare
gli avvisi.

**Da sapere**: il punto di ritorno si salva quando fai `/aggiorna`. Se non hai ancora fatto un
aggiornamento con questa versione, `/aggiorna indietro` ti dice che non c'è nulla da annullare.
Le modifiche ai tuoi file non si perdono: se un tuo file è toccato anche dall'aggiornamento,
il ritorno si ferma e te lo dice, invece di forzare. Dopo il ritorno, chiudi e riapri Claude
Code. Come si rilascia una versione, per chi mantiene Arturo o ne fa un fork, ora è scritto
in `docs/manutenzione.md`.

## 2026-09-16 — Cosa non è neutro, e cosa Arturo promette

**Cosa cambia**: il README si apre con tre sezioni nuove. **In breve** dice per chi è Arturo e come
cominciare in tre passi. **Cosa non è neutro** dice che Claude Code è un servizio a pagamento di
un'azienda privata, che quello che scrivi passa dai suoi server, e che un aggiornamento di Arturo è
codice di altri che gira sul tuo computer. **Impegni** dice cosa puoi aspettarti: repository
pubblico e MIT, niente telemetria, Arturo in italiano, e un avviso scritto se lo sviluppo si ferma.

**Il principio dietro**: chi usa uno strumento ha diritto di sapere chi lo controlla e cosa gli
viene promesso, prima di dipenderne. È lo stesso principio del capitolo 00 del curriculum, portato
sulla prima pagina.

**Da sapere**: `/inizio` scarica e applica gli aggiornamenti quando apri un progetto. Se preferisci
decidere tu ogni volta, usa `/aggiorna`, che ti chiede conferma prima di applicare.

## 2026-09-16 — L'avviso di aggiornamento, `/aggiorna` e `/guidami`

**Cosa cambia**: all'avvio della sessione Arturo ti dice quando c'è una versione nuova, come fa
Claude Code: `ARTURO: c'e' un aggiornamento (3 commit): scaricalo con /aggiorna`. Il comando
**`/aggiorna`** ti mostra cosa arriva, controlla che non travolga i file che hai modificato tu e
applica solo dopo il tuo sì. Arriva anche **`/guidami`**: guarda gli ultimi handoff e le
conversazioni recenti e ti propone tre o quattro cose che ha senso fare adesso, con il motivo e il
primo passo, scartando quello che nel frattempo hai già fatto.

**Il principio dietro**: il controllo degli aggiornamenti leggeva solo quello che era già sul disco.
Senza un `git fetch` restava fermo per sempre, e chi non lanciava `/inizio` non vedeva mai una
novità: il canale c'era, ma non arrivava a nessuno. Ora il fetch parte da solo all'avvio, in
background e al massimo ogni sei ore, così l'avvio non aspetta la rete.

**Da sapere**: dopo un aggiornamento, chiudi e riapri Claude Code. Comandi, hook e skill si leggono
all'avvio della sessione: finché non riapri, quello che è appena arrivato non c'è.

---

## 2026-09-16 — Il prompt prima del brief, e il promemoria a ogni richiesta

**Cosa cambia**: `prompt-master` non mostra più solo il brief. Prima mostra il **prompt**: la tua
richiesta riscritta come Arturo la eseguirà, in una o due frasi. Poi il brief, come prima. E l'hook
`inject-now.sh` aggiunge a ogni messaggio una riga che ricorda la regola, così non vive solo nel
`CLAUDE.md`.

**Il principio dietro**: un brief dice cosa l'assistente farebbe, non da quale lettura della tua
richiesta nasce. Se ha capito un'altra cosa, il brief ti sembra comunque sensato e te ne accorgi a
lavoro finito. Il prompt mostrato sposta il controllo all'inizio, dove costa una riga.

**Per spegnerlo**: cancella il blocco `cat` finale di `hooks/inject-now.sh`. Se l'aderenza alla
regola non migliora, il promemoria va tolto, non irrobustito: sarebbe uno scaffold che non
compensa niente.

---

## 2026-09-13 — Seconda passata: dati, sincronizzazione, audit e licenza

**Cosa cambia**: la guardia sui dati riconosce `docker compose -f … down -v` e non si fa ingannare da un `WHERE` dentro una stringa SQL. Se crei un tuo repository privato, `/setup` tiene Arturo come `upstream` e `/inizio` ne scarica gli aggiornamenti, così `/novita` continua a raccontarli. `/fine` non committa con il validate rosso, segnala gli errori di staging e ritenta i push rimasti indietro. L'audit legge i path fra virgolette e controlla anche statusline e `defaultMode`. I tool GitHub via MCP passano da soli solo quando leggono. `/novita` segna ogni entry appena raccontata, per data e titolo, così una lettura interrotta non ne salta nessuna. Arturo ha ora una licenza MIT (`LICENSE`).

**Il principio dietro**: una guardia che cede a una variante comune del comando non protegge, e un canale di aggiornamento che perde una voce non informa. I controlli si scrivono sul comportamento vero, non sulla forma più comoda da riconoscere.

---

## 2026-09-13 — Guardie aggiornate, errori visibili

**Cosa cambia**: Arturo distingue il vero hostname da userinfo, porta e sottostringhe. Un URL che sembra interno può quindi essere esterno. Il dispatcher trasforma crash e output spurio delle guardie in una richiesta di conferma. Il gate di validazione conserva il codice del comando che produce l'output: un test fallito ferma il lavoro.

**Tre porte chiuse**: un file di sblocco creato con Write o Edit chiede conferma come quello creato da shell, altrimenti l'assistente potrebbe sbloccarsi da solo. `gh api` chiede conferma quando scrive: mutazioni GraphQL, query lette da file, POST anche impliciti. `/fine` scrive l'handoff solo nello store della config e lo sincronizza solo verso un remote privato: in un progetto pubblico decisioni e note non entrano più nella storia Git.

**Potature**: spariscono i wrapper di comandi, skill e agenti approvati come duplicati, oltre al content guard GitHub e ai controlli PostToolUse non vincolanti. Restano le guardie distruttive e gli strumenti pedagogici.

**Il principio dietro**: una guardia deve identificare il destinatario reale. Un controllo deve riportare l'esito reale. Se non può provarlo, deve fermarsi.

---

## 2026-09-02 — La porta e la procedura: description, when_to_use e le sezioni "Freni"

**Cosa cambia**: ogni skill ha ora due campi in testa. `description` dice in una frase che cosa
la skill produce; `when_to_use` dice quando si accende: le frasi che dici davvero, i casi in cui
NON si accende e a chi passa la palla. Chiude sempre con "Segui tutti i passi nell'ordine: non
prendere scorciatoie basandoti su questa description". Nel corpo, la prima cosa dopo il titolo è
un passo o un prerequisito, non una spiegazione; le regole che non si possono saltare stanno sotto
un'intestazione propria, `## Freni` o `## Importante`. Due skill nuove: `prompt-master` (mostra un
brief di otto righe prima di ogni lavoro: obiettivo, output, vincoli, quando è fatto, assunzioni,
cosa chiarire) e `italiano-semplificato` (riscrive un testo con frasi corte e senza burocratese).
`/setup` propone entrambe le regole nel tuo `CLAUDE.md`; `/inizio` fa il pull con `--autostash`,
così un file sporco non blocca più l'aggiornamento.

**Il principio dietro**: il modello legge la `description` per decidere se una skill si applica.
Se lì trova i passi, li esegue senza aprire il corpo, saltando le regole. Quindi la porta dice
solo *se entrare*; la procedura sta dentro. E due domande valgono più di dieci regole: "se un
agente leggesse solo la description, cosa farebbe?" (deve rispondere: decide se serve) e "cosa
farebbe un agente pigro se questa skill non esistesse?" (il corpo deve impedire proprio quello).
Idee prese da `gsarig/skills`, applicate qui alla lettera.

**A chi serve**: a chi scrive o modifica una skill, e a chi si chiede perché una skill non è
partita quando doveva: il primo sospetto è la frase in `when_to_use`. Prova: `/sparring` sul
principio "la porta e la procedura" con una skill che usi spesso.

---

## 2026-08-19 — Chiedere bene: il capitolo 01 e i punti dove l'harness lo pretende

**Cosa cambia**: il curriculum ha un secondo capitolo disponibile,
`docs/principi/01-chiedere-bene.md`: la forma di una richiesta che funziona (da dove
parto, cosa è cambiato, cosa chiedo) e come si dichiara che il lavoro è finito. In più tre
comandi ora lo pretendono dove serve: `/discovery` chiede che i criteri di successo siano
risultati osservabili e non intenzioni, `/write-plan` fa aprire ogni fase con l'effetto che
produce, `/debug` chiede che l'ipotesi sia formulata in modo da poter essere smentita da una
verifica sì/no. Gli agenti che scrivono (`drafter`, `synthesizer`) mettono la conclusione in
cima invece che in fondo.

**Il principio dietro**: il modello risponde alla domanda che gli hai fatto, non a quella che
avevi in testa. Quando il contesto manca, se lo inventa in modo convincente. Formulare la
richiesta è la parte del lavoro che resta tua, non scade con la versione dello strumento, e
vale anche con le persone. L'altra metà dello stesso principio è dire come si riconosce che è
fatto: senza un risultato osservabile, "fatto" è un'opinione.

**Ti riguarda se**: ti è capitato di ricevere una risposta ben scritta e fuori bersaglio, o
di accorgerti a lavoro finito che "finito" voleva dire due cose diverse per te e per
l'assistente. La numerazione del curriculum è cambiata: i tre capitoli annunciati prima
(rail, orchestrazione, memoria) sono ora 02, 03 e 04.

**Per provarlo**: leggi `docs/principi/01-chiedere-bene.md` (sono dieci minuti), poi
`/sparring chiedere bene` per riscrivere insieme una richiesta vera, magari una che era
andata storta.

---

## 2026-08-17 — Nasce il canale novità, lo sparring e il curriculum dei principi

**Cosa cambia**: Arturo ora è un harness che ti tiene aggiornato. Tre pezzi nuovi:
`/novita` (questo canale: dopo ogni aggiornamento ti racconta cosa è cambiato e perché),
`/sparring` (una sessione guidata che parte da un principio e lo prova sui TUOI casi
d'uso, con esperimenti piccoli e reversibili), e la cartella `docs/principi/`, il
curriculum: i principi dell'usare bene un'AI, spiegati in semplice, per chi non fa un
mestiere tecnico.

**Il principio dietro**: uno strumento che impari una volta sola invecchia con te. Questo
campo cambia in fretta: quando un modo di lavorare nuovo diventa importante, l'harness si
aggiorna per tutti, e tu scopri la novità con il suo perché, non con un changelog di
sigle.

**Ti riguarda se**: usi Arturo e vuoi che continui a valere anche fra sei mesi; oppure
sei all'inizio e vuoi una strada per imparare i principi, non solo i comandi.

**Per provarlo**: leggi il primo capitolo del curriculum,
`docs/principi/00-chi-possiede-lo-strumento.md`: parte dalla domanda che viene prima di
ogni comando: di chi è lo strumento che stai imparando? Poi, se vuoi, `/sparring`.
