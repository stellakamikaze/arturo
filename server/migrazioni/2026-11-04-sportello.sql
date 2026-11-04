-- Lo sportello delle segnalazioni (4/11/2026, #3925): ricevuta col codice, pacchetto tecnico, stato e risposta.
-- Le righe che ci sono prendono i default: stato "ricevuta", nessun codice (la persona non può leggere la
-- risposta delle segnalazioni partite prima), nessun pacchetto.
-- Prima: export della tabella e segnalibro di time travel letti, e il sì di Federico (freno del D1). Ordine:
-- migrazione, poi il Worker, poi il client. Si applica con
--   npx wrangler@4 d1 execute arturo --remote --file server/migrazioni/2026-11-04-sportello.sql
ALTER TABLE segnalazioni ADD COLUMN origine TEXT NOT NULL DEFAULT 'segnala';
ALTER TABLE segnalazioni ADD COLUMN pacchetto TEXT NOT NULL DEFAULT '';
ALTER TABLE segnalazioni ADD COLUMN codice_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE segnalazioni ADD COLUMN stato TEXT NOT NULL DEFAULT 'ricevuta';
ALTER TABLE segnalazioni ADD COLUMN risposta TEXT NOT NULL DEFAULT '';
ALTER TABLE segnalazioni ADD COLUMN versione_fix TEXT NOT NULL DEFAULT '';
ALTER TABLE segnalazioni ADD COLUMN aggiornata TEXT NOT NULL DEFAULT '';
ALTER TABLE segnalazioni ADD COLUMN seguiti TEXT NOT NULL DEFAULT '[]';
