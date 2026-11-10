-- Il contatto di chi segnala (10/11/2026): nome ed email che la persona dà una volta con `arturo contatto`, perché
-- gli sviluppatori di Arturo possano ricontattarla sulle sue segnalazioni. Le righe che ci sono restano senza contatto.
-- Prima: export della tabella e segnalibro di time travel letti, e il sì di chi mantiene Arturo (freno del D1).
-- Ordine: migrazione, poi il Worker, poi il client. Si applica con
--   npx wrangler@4 d1 execute arturo --remote --file server/migrazioni/2026-11-10-contatto.sql
ALTER TABLE segnalazioni ADD COLUMN contatto_nome TEXT NOT NULL DEFAULT '';
ALTER TABLE segnalazioni ADD COLUMN contatto_email TEXT NOT NULL DEFAULT '';
