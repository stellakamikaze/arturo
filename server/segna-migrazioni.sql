-- Segna come già applicate le migrazioni di migrazioni/ (revisione del 22/11/2026, A4). Dal 23/11/2026 le migrazioni
-- passano da `wrangler d1 migrations apply`, che tiene in d1_migrations quelle fatte. Questo file serve due volte:
-- - un D1 nuovo, appena creato con schema.sql: lo schema ha già tutte le colonne, e le migrazioni fallirebbero;
-- - il D1 vero di Arturo, una volta sola: le tre migrazioni qui sotto le aveva già applicate `d1 execute`.
-- Si applica con
--   npx wrangler@4 d1 execute arturo --remote --file server/segna-migrazioni.sql
-- Ogni migrazione nuova entra anche qui, nella stessa modifica: il caso QM2 di test-sql.mjs lo controlla.
CREATE TABLE IF NOT EXISTS d1_migrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
INSERT OR IGNORE INTO d1_migrations (name) VALUES
  ('2026-10-25-feedback-senza-voce.sql'),
  ('2026-11-04-sportello.sql'),
  ('2026-11-10-contatto.sql');
