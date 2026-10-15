# Promemoria per chi cura lo strato di {{ORGANIZZAZIONE}}

La guida completa è in Arturo: `~/.claude/docs/referente.md`.

- **Cosa cambi qui, arriva ai colleghi.** Voce in `plugins/strato/skills/voce/regole.md`,
  chi siamo in `plugins/strato/ORGANIZZAZIONE.md`, dati riservati in
  `plugins/strato/dati-riservati.txt`, un lavoro ricorrente in una cartella nuova sotto
  `plugins/strato/skills/`.
- **Esempi da adattare** (posta, recap, anteprima prima dell'invio) in `esempi/`: non sono
  attivi finché non li copi in `plugins/strato/`.
- **Prima di pubblicare, prova:** `claude --plugin-dir plugins/strato`.
- **Per pubblicare:** `/strato pubblica`. I colleghi ricevono la modifica con `/aggiorna`.
- **Mai nello strato:** password, token, dati personali. Il repository lo leggono tutti i colleghi.
- **Un nuovo collega:** invitalo al repository, poi gli basta `/strato installa <indirizzo>`.
