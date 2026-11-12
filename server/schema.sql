-- Il database D1 del server di Arturo. Nessuna colonna per l'IP, per scelta.
CREATE TABLE IF NOT EXISTS eventi (
  giorno TEXT NOT NULL,           -- il giorno dell'evento sul computer della persona, mai l'ora
  ricevuto_giorno TEXT NOT NULL,  -- il giorno in cui il server l'ha ricevuto, per i tetti
  installazione TEXT NOT NULL,    -- id casuale creato da Arturo: non è anonimo, vedi docs/privacy.md
  versione TEXT NOT NULL,
  sistema TEXT NOT NULL,
  evento TEXT NOT NULL,
  valore TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS eventi_giorno ON eventi (giorno, evento);
CREATE INDEX IF NOT EXISTS eventi_installazione ON eventi (installazione, ricevuto_giorno);
CREATE INDEX IF NOT EXISTS eventi_ricevuti ON eventi (ricevuto_giorno);

CREATE TABLE IF NOT EXISTS segnalazioni (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ricevuta TEXT NOT NULL,
  tipo TEXT NOT NULL,
  titolo TEXT NOT NULL,
  testo TEXT NOT NULL,
  versione TEXT NOT NULL DEFAULT '',
  sistema TEXT NOT NULL DEFAULT '',
  installazione TEXT NOT NULL DEFAULT '',
  email_inviata INTEGER NOT NULL DEFAULT 0,
  -- Lo sportello (4/11/2026, server/migrazioni/2026-11-04-sportello.sql): da dove arriva, il pacchetto tecnico
  -- (JSON, svuotato dopo 90 giorni), l'hash del codice della ricevuta, stato e risposta di chi mantiene Arturo,
  -- i seguiti della persona (JSON).
  origine TEXT NOT NULL DEFAULT 'segnala',
  pacchetto TEXT NOT NULL DEFAULT '',
  codice_hash TEXT NOT NULL DEFAULT '',
  stato TEXT NOT NULL DEFAULT 'ricevuta',
  risposta TEXT NOT NULL DEFAULT '',
  versione_fix TEXT NOT NULL DEFAULT '',
  aggiornata TEXT NOT NULL DEFAULT '',
  seguiti TEXT NOT NULL DEFAULT '[]',
  -- Il contatto di chi segnala (10/11/2026, server/migrazioni/2026-11-10-contatto.sql): nome ed email dati con
  -- `arturo contatto`, facoltativi. Si cancellano col ritiro e con la riga, dopo 12 mesi.
  contatto_nome TEXT NOT NULL DEFAULT '',
  contatto_email TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS contatori (
  giorno TEXT NOT NULL,
  chiave TEXT NOT NULL,
  n INTEGER NOT NULL,
  PRIMARY KEY (giorno, chiave)
);

-- Il modulo di feedback del sito (16/10/2026): solo messaggi scritti. La colonna voce è uscita il 25/10/2026
-- (server/migrazioni/2026-10-25-feedback-senza-voce.sql): nessun vocale era mai arrivato.
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ricevuto TEXT NOT NULL,
  tipo TEXT NOT NULL,
  testo TEXT NOT NULL DEFAULT '',
  email TEXT NOT NULL DEFAULT ''
);

-- Lancillotto (25/10/2026). Il Worker la crea da solo alla prima richiesta (archivio.js, TABELLA_LANCILLOTTO).
CREATE TABLE IF NOT EXISTS eventi_lancillotto (
  giorno TEXT NOT NULL, ricevuto_giorno TEXT NOT NULL, installazione TEXT NOT NULL, versione TEXT NOT NULL,
  sistema TEXT NOT NULL, evento TEXT NOT NULL, valore TEXT NOT NULL DEFAULT ''
);
