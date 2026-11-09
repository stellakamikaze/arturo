# Lo schema delle righe di /monitor

Ogni ponte consegna a /monitor **righe JSON**, una per riga, senza prosa in mezzo. `righe.py` le
valida, aggiunge il fingerprint e scarta le righe fuori schema dicendo il perché.

```bash
python3 $ARTURO_CODICE/bin/monitor/righe.py consegna.jsonl > valide.jsonl
```

## Riga item: una cosa da fare

```json
{"tipo":"item","fonte":"email","id_sorgente":"1a0f7a23d0379a35","data":"2026-11-03","scadenza":"2026-11-07","progetto":"sito","riassunto":"Marta aspetta le foto per la pagina chi siamo","urgenza":"giallo","promessa":null,"extra":{"mittente":"marta@example.com"}}
```

| Campo | Obbligatorio | Contenuto |
|---|---|---|
| `tipo` | sì | `item` |
| `fonte` | sì | il nome del ponte: minuscole, cifre e trattini |
| `id_sorgente` | sì | l'ID che apre la cosa nella fonte: il thread, il file, il numero del todo |
| `data` | sì | `AAAA-MM-GG` del messaggio o del record da cui nasce |
| `scadenza` | no | `AAAA-MM-GG` assoluta, calcolata dalla data del messaggio; `null` se non c'è |
| `progetto` | no | lo slug del progetto, oppure `null` |
| `riassunto` | sì | una riga: chi aspetta cosa da chi |
| `urgenza` | sì | `rosso`, `giallo` o `verde` |
| `promessa` | no | `{"a_chi":"…","cosa":"…","entro":"AAAA-MM-GG"}`, solo per un impegno preso dalla persona |
| `extra` | no | i campi propri della fonte |
| `fp` | no | il fingerprint, se `<fonte>:<id_sorgente>` non basta a distinguere (vedi sotto) |

`righe.py` aggiunge `fp`, se manca, e `hash`. Un campo che non sta in questa tabella fa scartare la
riga: così una parte personale non fa passare nel giro generico i suoi campi (per esempio le cifre).

## Il fingerprint

È la stringa che riconosce la stessa cosa da un giro all'altro: `<fonte>:<id>[:<id>...]`, solo con
ID stabili della fonte, mai con parole del riassunto. Di serie vale `<fonte>:<id_sorgente>`. Un
ponte che da un solo thread ricava due cose da fare le distingue con un pezzo in più, stabile anche
lui: `email:1a0f7a23d0379a35:2026-11-03`. Una stringa con spazi è testo libero e si rifiuta
(`fingerprint.py`). L'hash sono i primi 8 caratteri dell'md5 della stringa.

## Riga di copertura: quanto ha letto

Una per fonte, l'ultima della sua consegna:

```json
{"tipo":"copertura","fonte":"email","listati":42,"letti":40,"troncato":true,"motivo":"due thread non si aprono","dettaglio":"non letti: 1b2c…, 1d4e…"}
```

`letti` conta gli elementi aperti nel contenuto, non solo negli elenchi. Con `troncato: true` serve
il `motivo`. Una fonte senza cose da fare consegna lo stesso la copertura: "letta, niente da fare" e
"non letta" sono due stati diversi, e senza copertura `righe.py` dice che manca. Una fonte che non consegna
niente si vede solo se il giro passa le fonti scelte: `righe.py --attese email,task`. `letti` minore di
`listati` vale solo con `troncato: true`. Lo stesso `fp` due volte nella stessa consegna è uno scarto.
