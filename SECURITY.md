# Sicurezza

## Cosa segnalare qui

Segnala in privato se trovi:

- un segreto o un dato personale dentro il repository (una password, un token, una chiave, un nome o un indirizzo che non dovrebbe esserci);
- un modo per aggirare una guardia di Arturo;
- un modo per far installare un aggiornamento senza la firma dei rilasci, da solo o con `/aggiorna`.

I rilasci di Arturo sono tag firmati con una chiave SSH ed25519, impronta
`SHA256:IoYVqxkPVwvac2DtQb0dBx7HwUjA7077mDpLDqwKMKY`. La chiave pubblica è in
`firme/rilasci.allowed_signers`. L'aggiornamento automatico e `/aggiorna` installano solo l'ultimo
tag che questa chiave ha firmato, letta dalla copia già installata, e mai `main`. Se l'ultimo tag non
ha una firma valida, Arturo dice «possibile compromissione: non aggiornare, segnala a chi mantiene
Arturo»: è il caso da segnalare qui.

Il motivo è semplice: una segnalazione pubblica avvisa anche chi potrebbe
approfittarne.

## Come segnalare

Usa il pulsante **«Report a vulnerability»** nella scheda Security del
repository:
<https://github.com/stellakamikaze/arturo/security/advisories/new>

Descrivi cosa hai trovato e dove. Se puoi, aggiungi i passi per riprodurlo.

## Cosa succede dopo

La segnalazione resta privata finché il problema non è chiuso. Nessuna
promessa di tempi: vale quanto detto nella sezione «Autore e manutenzione»
del README. Le issue vengono lette, ma non c'è obbligo di risposta né di fix.

## Cosa NON serve segnalare qui

Un falso positivo di una guardia — un comando legittimo che chiede conferma —
non è un problema di sicurezza. Quello si segnala con `/segnala`, oppure in una
issue normale col comando esatto (vedi il Troubleshooting nel README).
