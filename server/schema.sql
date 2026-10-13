-- Il database D1 del server di Arturo. Nessuna colonna per l'IP, per scelta.
CREATE TABLE IF NOT EXISTS eventi (
  giorno TEXT NOT NULL,           -- il giorno dell'evento sul computer della persona, mai l'ora
  ricevuto_giorno TEXT NOT NULL,  -- il giorno in cui il server l'ha ricevuto, per i tetti
  installazione TEXT NOT NULL,    -- id casuale creato da Arturo, non legato alla persona
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
  email_inviata INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS contatori (
  giorno TEXT NOT NULL,
  chiave TEXT NOT NULL,
  n INTEGER NOT NULL,
  PRIMARY KEY (giorno, chiave)
);
