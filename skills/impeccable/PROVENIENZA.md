Copia fissata della skill `impeccable` da pbakaus/impeccable, release `skill-v4.6.0`, commit
`8a0e198da34ebc5b936a9d5975fb7a3b1cf353b7` (`8a0e198da34e`, 16/10/2026). Licenza Apache-2.0 (`LICENSE`), avvisi di
terzi in `NOTICE.md` (i riferimenti iOS e Android derivano da ehmo/platform-design-skills, MIT).

Cosa c'è: `SKILL.md` e `reference/` di upstream, invariati nel corpo.

Modifiche di Arturo:
1. `description` e `when_to_use` in italiano: Arturo parla italiano, e il modello sceglie la skill da quei due campi.
2. Manca la cartella `scripts/` di upstream (1,7 MB). Il suo launcher scarica da GitHub ed esegue un binario al primo
   uso. Arturo non installa programmi che `/setup` non dichiara, quindi la skill gira nella modalità che upstream
   prevede quando il launcher manca («Launcher unavailable»): legge `PRODUCT.md` e `DESIGN.md` del progetto e lavora
   senza il rilevatore automatico dei difetti. Una nota in testa alla sezione Setup di `SKILL.md` lo dice al modello.
   Chi vuole la versione completa la installa da upstream, sapendo che scarica un eseguibile.

Non si aggiorna da sola: una versione nuova si scarica, si rilegge e si copia qui a mano, ripetendo le due modifiche.
