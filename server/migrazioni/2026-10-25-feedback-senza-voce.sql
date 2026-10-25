-- Solo messaggi scritti (Federico, 25/10/2026). La colonna voce segnava un vocale passato a Telegram:
-- nel D1 vero tutte le righe avevano 0. Il codice non la scrive più dal 24/10/2026 (dev 27ba147).
-- Prima: export della tabella e segnalibro di time travel letti. Si applica con
--   npx wrangler@4 d1 execute arturo --remote --file server/migrazioni/2026-10-25-feedback-senza-voce.sql
ALTER TABLE feedback DROP COLUMN voce;
