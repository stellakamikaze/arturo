# Il ramo sync: i dati di passaggio fuori da `main`

Questa pagina dice perché handoff, stati dei progetti e memoria stanno su un ramo a parte, `sync`, e come
un computer passa a quel ramo. Vale per chi tiene `~/.claude` come repository privato su GitHub e lo usa su
più computer. Il codice sta in `bin/sync_transito.py`, il banco in `tests/test_sync_transito.py` (ST01-ST16).

## Perché un ramo a parte (D5, 22/11/2026)

`/fine` salva a ogni chiusura, anche a ogni rotazione. Prima ogni salvataggio era un commit "session sync"
su `main`, con un push. Su una config con tre computer erano fino a 128 commit al giorno, e quasi tutti
toccavano gli stessi pochi file: il registro di Melchior, `data/progetti/stati.json`,
`data/handoffs/INDEX.md`, gli handoff, le note di memoria. Per questo servivano quattro merge driver, e un
push rifiutato rifaceva il pull.

Questi sono dati di passaggio: cambiano a ogni sessione e servono agli altri computer, non alla storia
della config. `main` resta per le cose che decidi tu: regole, hook, skill, comandi, `settings.json`. I dati
di passaggio vanno sul ramo `sync`.

## Come è fatto

- **I file restano dove sono.** Hook e script li cercano in `~/.claude/data/...`, e lì restano. Un secondo
  git dentro la stessa cartella li traccia: il git dir è `~/.claude/.git-sync`, il work tree è `~/.claude`,
  il ramo è `sync` sullo stesso `origin` di `main`.
- **Un elenco solo** dice quali path passano dal ramo sync: `data/transito.paths`. Oggi sono
  `data/handoffs`, `data/progetti/stati.json` e `data/memory`. Lucchetti, copie `.bak-`, cartelle
  rigenerabili e file sensibili (`.env`, chiavi, `credentials.json`) restano fuori anche se stanno sotto
  quei path.
- **Un giro alla volta per computer.** Il lucchetto `.git-sync/lock` tiene il pid di chi lavora. Un giro
  che trova il lucchetto preso esce senza fare niente. Un lucchetto più vecchio di 10 minuti è di un
  processo morto, e il giro dopo lo riprende.
- **Al massimo un push al minuto.** Il commit locale parte sempre. Il push parte solo se dall'ultimo
  (`.git-sync/ultimo-push`) è passato un minuto, altrimenti aspetta il giro dopo.
- **I dati degli altri arrivano ogni 5 minuti** (24/11/2026). Un giro col ramo già spinto fa fetch e rebase di
  `origin/sync` se dall'ultimo fetch (`.git-sync/ultimo-fetch`) sono passati 5 minuti
  (`SYNC_TRANSITO_ENTRATA`, in secondi). Così una macchina che non scrive niente riceve lo stesso le note
  delle altre. Dentro i 5 minuti un giro senza commit nuovi non usa la rete.
- **Windows** (24/11/2026). Il ramo sync prende `core.autocrlf` da main, perché il work tree è lo stesso:
  con `false` fisso, su Windows ogni file in CRLF risultava cambiato. I path di `git add` e `git commit --only`
  passano da un file (`--pathspec-from-file`): nella riga di comando mille note superano i 32.767 caratteri di
  Windows (WinError 206). Casi ST18 e ST19 del banco. I collegamenti simbolici che main tiene (modo 120000)
  restano fuori dal ramo: su Windows sono file di testo col nome della destinazione, e sul Mac il rebase si
  fermerebbe sul collegamento vero. Se uno è già entrato, il giro lo toglie dall'indice (caso ST20).
- **Solo su un repository privato.** Se `origin` è il repository pubblico di Arturo, o se manca, o se
  `gh` non dice `PRIVATE`, i commit restano su questo computer. Il ramo sync non va mai sul repository
  pubblico.
- **I segreti si fermano prima del commit.** Il giro passa le righe nuove alla guardia dei segreti
  (`hooks/commit-secret-gate.py`). Se la guardia trova una chiave, il giro si ferma con exit 7 e nomina il
  file, senza mostrare il valore.
- **Le cancellazioni in massa si fermano.** Se un giro trova più di 25 file cancellati, il commit non
  parte (exit 4). Di solito è un pull di `main` fatto a mano, che ha tolto i file dal disco. Dopo aver
  guardato le cancellazioni, `SYNC_TRANSITO_CANCELLAZIONI_OK=1` lascia passare il giro.
- **Gli stessi merge driver.** Il ramo sync legge lo stesso `.gitattributes` di `main` e copia da `main`
  la config dei driver: `stati.json` e i registri si uniscono senza conflitti.
- **I conflitti si risolvono da soli** (24/11/2026). Se due macchine cambiano lo stesso file, il rebase non
  si ferma più. Una nota di `data/memory` tiene le righe di tutte e due le versioni, e qualche riga può
  uscire doppia. Se una macchina l'ha cancellata e l'altra cambiata, resta la cambiata. Un handoff, e ogni
  altro file, prende la versione scritta per ultimo, secondo la data d'autore del commit. La versione che
  perde resta nella storia del ramo. Prima il giro usciva 4 a ogni minuto: il 24/11 un Mac ha tenuto fermi
  20 commit. Caso ST21 del banco.
- **Un blocco lungo si segnala.** Se il giro esce 4 per altri motivi, `.git-sync/bloccato-dal` tiene l'ora
  del primo giro fermo. Dopo 10 minuti il giro stampa una volta sola la riga `AVVISO:`, e `--stato` dice
  `BLOCCATO`. Il primo giro riuscito toglie il segno. Caso ST22.

## Chi lancia cosa

```
/fine (bin/fine-coda.py, passo 11)   sync_transito.py --subito      commit, push se è passato il minuto
giro ogni minuto (facoltativo)       sync_transito.py --giro        lo stesso, senza aspettare /fine
pull della config, prima             sync_transito.py --prima-del-pull main
pull della config, dopo              sync_transito.py --dopo-il-pull <HEAD di main prima del pull>
a mano                               sync_transito.py --stato       commit non spinti, ultimo push, lucchetto
```

- **`/fine`.** Sui computer che hanno `.git-sync`, la coda di `/fine` lascia fuori dal commit su `main`
  i path di transito e chiama `--subito` alla fine. Sui computer senza `.git-sync` la coda fa come prima:
  la migrazione va un computer alla volta.
- **`--prima-del-pull`.** Committa sul ramo sync i path di transito com'è il disco, e scrive il segno
  "pull in corso", che ferma i giri fino al passo dopo. Se il pull di `main` sta per togliere un path di
  transito cambiato qui, il file torna alla copia di `main`: la copia nuova è già nel ramo sync, e così
  l'autostash del pull non va in conflitto.
- **`--dopo-il-pull <sha>`.** Rimette su disco i file che `main` ha smesso di tracciare, dal ramo sync.
  Ripristina solo i file che `main` adesso ignora: una cancellazione vera, come la pulizia degli handoff
  vecchi su un altro computer, resta. Poi fa commit, fetch e rebase del ramo sync, anche dentro il minuto,
  così i dati degli altri computer arrivano subito.
- **Il giro ogni minuto.** È facoltativo: senza, i dati partono a ogni `/fine`. Su un Mac lo fa un
  LaunchAgent con `StartInterval` a 60 secondi, che lancia `bin/sync_transito.py --giro` dalla cartella
  del codice di Arturo. Su Windows serve un'attività pianificata, che
  Arturo non scrive ancora. Arturo non installa il giro da solo: lo arma la config della persona.

## Limiti di oggi

- **Il pull di `/inizio` di Arturo non chiama ancora il ramo sync.** `bin/aggiorna-applica.sh`, in modo
  `sync`, aggiorna solo `main`. Su un computer migrato i dati degli altri computer arrivano al primo giro
  che spinge, perché il push fa prima un rebase su `origin/sync`, oppure al giro in entrata dei 5 minuti. La config che chiama
  `--prima-del-pull` e `--dopo-il-pull` dal suo pull li riceve subito.
- **Il commit che toglie i path da `main` non lo fa Arturo.** Finché `main` traccia ancora i path di
  transito, gli stessi file stanno su tutti e due i rami: funziona, e `main` riceve solo i commit di chi
  non ha migrato. Il commit che li toglie (passo 5 qui sotto) è un passo della persona.

## Come si migra

Si migra un computer alla volta. Ogni computer lavora come prima finché non ha `.git-sync`.

1. **La prova.** Da un Terminale, con la sessione chiusa:

   ```bash
   python3 "$(cat ~/.claude/arturo/radice)/bin/sync_transito.py" --migra --prova
   ```

   `~/.claude/arturo/radice` contiene la cartella del codice di Arturo, che l'avvio scrive. La prova
   stampa il git dir, i path di transito, l'`origin` e se il push partirà. Non scrive niente.
2. **Il primo computer.** Lo stesso comando senza `--prova`. Lo script crea `.git-sync`, lo esclude da
   `main` (`.git/info/exclude`), crea il ramo `sync` con i file di transito come sono sul disco e lo
   spinge su `origin`.
3. **Gli altri computer.** Prima un pull della config, poi lo stesso `--migra`. Lo script trova il ramo
   `sync` su `origin` e lo aggancia senza togliere niente: un file che manca sul disco torna dal ramo, un
   file diverso si fonde a tre con la copia di `main` come base. In conflitto resta la copia di questo
   computer, e quella del ramo resta nella sua storia. Il primo giro committa la differenza.
4. **Il giro ogni minuto**, se lo vuoi: il LaunchAgent o l'attività pianificata della sezione "Chi lancia
   cosa".
5. **Il commit su `main` che toglie i path.** Solo dopo che tutti i computer hanno fatto il passo 2 o il
   passo 3. Il commit mette i path di transito in `.gitignore` e li toglie dall'indice con
   `git rm --cached`: sul disco restano. Un computer che non ha migrato, al pull, perde quei file dal disco.
   Un computer migrato li ritrova con `--dopo-il-pull`. Guarda prima `git diff --cached --stat`.

Per tornare indietro prima del passo 5 basta togliere `.git-sync` da un computer: `main` non è cambiato, e
la coda di `/fine` torna a mettere i path di transito su `main`. Dopo il passo 5 serve anche un
`git revert` di quel commit.
