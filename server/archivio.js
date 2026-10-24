// L'archivio del server di Arturo: le query su D1. Separato da worker.js, che importa cloudflare:email,
// così test-sql.mjs prova le query vere su SQLite con node, senza Cloudflare.
import { LIMITI, ritenzione, calcolaIndietro } from "./logica.js";

// v2026-10-15: da qui /setup manda i suoi eventi alla telemetria.
const SETUP_DAL = "2026-10-15";

// Le statistiche delle guardie contano solo le installazioni che il server ha visto in almeno
// LIMITI.giorniGuardie giorni diversi (17/10/2026, #3507). Chiunque può mandare eventi con un id nuovo: un
// lotto di un giorno solo non deve bastare a far sembrare inutile una guardia. Il giorno è quello in cui il
// server ha ricevuto il lotto, che il client non sceglie.
// Dal 24/10/2026 lo stesso filtro vale per comandi, setup, versioni di Claude Code e aggiornamenti non applicati:
// sono i numeri che decidono cosa correggere, e un id inventato li spostava come spostava le guardie.
const VISTE = `installazione IN (SELECT installazione FROM eventi GROUP BY installazione
  HAVING COUNT(DISTINCT ricevuto_giorno) >= ${Number(LIMITI.giorniGuardie)})`;

export function archivio(db) {
  return {
    // Gli eventi del giorno di un'installazione. Il totale di tutte sta nel contatore "eventi".
    async contaEventi(installazione, giorno) {
      const r = await db.prepare("SELECT COUNT(*) AS n FROM eventi WHERE installazione = ? AND ricevuto_giorno = ?").bind(installazione, giorno).first();
      return r ? r.n : 0;
    },
    // Vero se dall'installazione non è mai arrivato niente: è la prima volta che Arturo gira lì.
    async installazioneNuova(installazione) {
      return !(await db.prepare("SELECT 1 AS x FROM eventi WHERE installazione = ? LIMIT 1").bind(installazione).first());
    },
    async scriviEventi(righe, ricevuto) {
      const giorno = ricevuto.slice(0, 10);
      const insert = db.prepare(
        "INSERT INTO eventi (giorno, ricevuto_giorno, installazione, versione, sistema, evento, valore) VALUES (?, ?, ?, ?, ?, ?, ?)");
      await db.batch(righe.map((x) => insert.bind(x.giorno, giorno, x.installazione, x.versione, x.sistema, x.evento, x.valore)));
    },
    async contaSegnalazioni(giorno) {
      const r = await db.prepare("SELECT COUNT(*) AS n FROM segnalazioni WHERE substr(ricevuta, 1, 10) = ?").bind(giorno).first();
      return r ? r.n : 0;
    },
    async salvaSegnalazione(s, ricevuta) {
      const r = await db.prepare(
        "INSERT INTO segnalazioni (ricevuta, tipo, titolo, testo, versione, sistema, installazione) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id")
        .bind(ricevuta, s.tipo, s.titolo, s.testo, s.versione, s.sistema, s.installazione).first();
      return r.id;
    },
    // Vero solo la prima volta che la chiave compare nel giorno: un avviso al giorno, non uno per lotto.
    async primaVolta(giorno, chiave) {
      const r = await db.prepare(
        "INSERT INTO contatori (giorno, chiave, n) VALUES (?, ?, 1) ON CONFLICT (giorno, chiave) DO UPDATE SET n = n + 1 RETURNING n")
        .bind(giorno, chiave).first();
      return r.n === 1;
    },
    // Un contatore del giorno: torna il valore dopo l'aggiunta. Tiene i tetti di eventi, email, avvisi, feedback e download.
    async incrementa(giorno, chiave, quanti = 1) {
      const r = await db.prepare(
        "INSERT INTO contatori (giorno, chiave, n) VALUES (?, ?, ?) ON CONFLICT (giorno, chiave) DO UPDATE SET n = n + excluded.n RETURNING n")
        .bind(giorno, chiave, quanti).first();
      return r.n;
    },
    async salvaFeedback(f, ricevuta) {
      const r = await db.prepare(
        "INSERT INTO feedback (ricevuto, tipo, testo, email) VALUES (?, ?, ?, ?) RETURNING id")
        .bind(ricevuta, f.tipo, f.testo, f.email).first();
      return r.id;
    },
    async segnaEmail(id) {
      await db.prepare("UPDATE segnalazioni SET email_inviata = 1 WHERE id = ?").bind(id).run();
    },
    // L'elenco corrente della deriva per installazione: le righe dopo l'ultimo `insieme:<n>`.
    // Il giorno: solo gli elenchi cambiati nella finestra. La settimana: anche quelli fermi ma non vuoti.
    async deriva(dal, al, settimana) {
      const marcatori = (await db.prepare(
        `SELECT e.installazione, e.rowid AS r, e.valore, e.giorno FROM eventi e
         JOIN (SELECT installazione, MAX(rowid) AS r FROM eventi WHERE evento = 'deriva' AND valore LIKE 'insieme:%' GROUP BY installazione) m
           ON e.rowid = m.r`).all()).results
        .filter((m) => (m.giorno > dal && m.giorno <= al) || (settimana && m.valore !== "insieme:0"));
      const conflitti = new Set((await db.prepare(
        "SELECT DISTINCT installazione FROM eventi WHERE evento = 'aggiorna' AND valore = 'conflitto' AND giorno > date(?, '-30 day') AND giorno <= ?")
        .bind(al, al).all()).results.map((x) => x.installazione));
      const fuori = [];
      for (const m of marcatori) {
        const valori = (await db.prepare(
          "SELECT valore FROM eventi WHERE installazione = ? AND evento = 'deriva' AND rowid > ? AND valore NOT LIKE 'insieme:%' ORDER BY rowid")
          .bind(m.installazione, m.r).all()).results.map((x) => x.valore);
        fuori.push({ installazione: m.installazione, valori, conflitto: conflitti.has(m.installazione) });
      }
      return fuori;
    },
    // Le installazioni rimaste indietro (calcolaIndietro in logica.js): la versione dell'ultimo evento di chi è
    // attivo negli ultimi giorni, e il primo giorno di ogni versione. Solo installazioni viste in più giorni.
    async indietro(al) {
      const tutte = async (sql, ...valori) => (await db.prepare(sql).bind(...valori).all()).results;
      const attive = await tutte(
        `SELECT e.installazione AS installazione, e.versione AS versione, m.ultima AS ultima FROM eventi e
         JOIN (SELECT installazione, MAX(rowid) AS r, MAX(giorno) AS ultima FROM eventi
               WHERE giorno > date(?, '-${Number(LIMITI.fermaGiorni)} day') AND giorno <= ? AND ${VISTE} GROUP BY installazione) m
         ON e.rowid = m.r`, al, al);
      const versioni = await tutte(
        `SELECT versione, MIN(giorno) AS prima FROM eventi WHERE giorno <= ? AND ${VISTE} GROUP BY versione`, al);
      return calcolaIndietro(attive, versioni, al);
    },
    // Il giorno dell'ultimo avviso con questa chiave, per non ripeterlo ogni mattina.
    async ultimoAvviso(chiave) {
      const r = await db.prepare("SELECT MAX(giorno) AS giorno FROM contatori WHERE chiave = ? AND giorno <> 'sempre'").bind(chiave).first();
      return r ? r.giorno : null;
    },
    // "Dove migliorare Arturo", per il riepilogo del lunedì e per /v1/riepilogo. Numeri e rapporti,
    // nessuna soglia che decide: il giudizio su cosa correggere spetta a chi legge. La finestra è di
    // 30 giorni, perché con poche installazioni una settimana non mostra niente. Dal 24/10/2026 vale per
    // tutto il blocco: prima setup e ritenzione contavano tutto lo storico, sotto un titolo che diceva 30 giorni.
    async miglioramento(al) {
      const tutte = async (sql, ...valori) => (await db.prepare(sql).bind(...valori).all()).results;
      const uno = async (sql, ...valori) => ((await db.prepare(sql).bind(...valori).first()) || { n: 0 }).n;
      const trenta = "giorno > date(?, '-30 day') AND giorno <= ?";
      return {
        indietro: await this.indietro(al),
        // L'ultima fase vista per installazione, se non è arrivata in fondo e tace da 3 giorni.
        setupFermi: await tutte(
          `SELECT e.valore AS valore, COUNT(*) AS n FROM eventi e
           JOIN (SELECT installazione, MAX(rowid) AS r FROM eventi WHERE evento = 'setup' AND ${VISTE} GROUP BY installazione) m ON e.rowid = m.r
           WHERE e.valore <> 'fine' AND e.giorno > date(?, '-30 day') AND e.giorno <= date(?, '-3 day')
             AND e.installazione NOT IN (SELECT installazione FROM eventi WHERE evento = 'setup' AND valore = 'fine')
           GROUP BY e.valore ORDER BY n DESC`, al, al),
        setupFiniti: await uno(
          `SELECT COUNT(DISTINCT installazione) AS n FROM eventi WHERE evento = 'setup' AND valore = 'fine' AND ${trenta} AND ${VISTE}`, al, al),
        setupIniziati: await uno(
          `SELECT COUNT(DISTINCT installazione) AS n FROM eventi WHERE evento = 'setup' AND ${trenta} AND ${VISTE}`, al, al),
        // Chi non ha mai lanciato /setup: installazioni nate da SETUP_DAL (il primo rilascio che manda
        // gli eventi di /setup) e negli ultimi 30 giorni, da almeno un giorno, senza nessun evento setup.
        // Prima di SETUP_DAL lo zero non vuol dire niente.
        setupMai: await uno(
          `SELECT COUNT(*) AS n FROM (SELECT installazione FROM eventi WHERE ${VISTE} GROUP BY installazione
             HAVING MIN(giorno) >= ? AND MIN(giorno) > date(?, '-30 day') AND MIN(giorno) <= date(?, '-1 day') AND SUM(evento = 'setup') = 0)`,
          SETUP_DAL, al, al),
        // Quante volte una guardia chiede, e quante volte la persona conferma.
        // Ogni numero dice quante installazioni lo producono.
        conferme: await tutte(
          `SELECT valore, SUM(evento = 'chiede') AS chiede, SUM(evento = 'confermata') AS confermata,
             COUNT(DISTINCT installazione) AS installazioni FROM eventi
           WHERE evento IN ('chiede', 'confermata') AND ${trenta} AND ${VISTE} GROUP BY valore ORDER BY chiede DESC LIMIT 20`, al, al),
        // Le stesse, sommate per guardia: block-dangerous (dal 22/10/2026) e commit-secret-gate (dal 23/10) mandano <guardia>.<regola>, e
        // con tante regole le altre guardie uscirebbero dalle prime 20 di `conferme` (#3799).
        confermeGuardie: await tutte(
          `SELECT CASE WHEN instr(valore, '.py.') > 0 THEN substr(valore, 1, instr(valore, '.py.') + 2) ELSE valore END AS valore,
             SUM(evento = 'chiede') AS chiede, SUM(evento = 'confermata') AS confermata,
             COUNT(DISTINCT installazione) AS installazioni FROM eventi
           WHERE evento IN ('chiede', 'confermata') AND ${trenta} AND ${VISTE} GROUP BY 1 ORDER BY chiede DESC LIMIT 20`, al, al),
        errori: await tutte(
          `SELECT valore, COUNT(*) AS n, COUNT(DISTINCT installazione) AS installazioni FROM eventi
           WHERE evento = 'errore' AND ${trenta} AND ${VISTE} GROUP BY valore ORDER BY n DESC LIMIT 20`, al, al),
        aggiornaStorti: await tutte(
          `SELECT versione, valore, COUNT(*) AS n FROM eventi
           WHERE evento = 'aggiorna' AND valore <> 'applicato' AND ${trenta} AND ${VISTE} GROUP BY versione, valore ORDER BY n DESC LIMIT 20`, al, al),
        // La finestra della ritenzione sta in ritenzione() (logica.js): per ogni soglia, le nate nei 30 giorni prima.
        ritenzione: ritenzione(await tutte(
          "SELECT installazione, MIN(giorno) AS prima, MAX(giorno) AS ultima FROM eventi WHERE giorno <= ? GROUP BY installazione", al), al),
        claude: await tutte(
          `SELECT valore, COUNT(DISTINCT installazione) AS n FROM eventi
           WHERE evento = 'claude' AND ${trenta} AND ${VISTE} GROUP BY valore ORDER BY n DESC LIMIT 20`, al, al),
      };
    },
    async riepilogo(dal, al, { settimana = false } = {}) {
      const gruppo = async (evento) => (await db.prepare(
        "SELECT valore, COUNT(*) AS n FROM eventi WHERE evento = ? AND giorno > ? AND giorno <= ? GROUP BY valore ORDER BY n DESC LIMIT 20")
        .bind(evento, dal, al).all()).results;
      const colonna = async (nome) => (await db.prepare(
        `SELECT ${nome} AS valore, COUNT(DISTINCT installazione) AS n FROM eventi WHERE giorno > ? AND giorno <= ? GROUP BY ${nome} ORDER BY n DESC LIMIT 20`)
        .bind(dal, al).all()).results;
      const uno = async (sql) => ((await db.prepare(sql).bind(dal, al).first()) || { n: 0 }).n;
      // I contatori senza id del giorno (24/10/2026): eventi scartati, avvisi Telegram ed email non partiti.
      const contatore = async (chiave) => ((await db.prepare(
        "SELECT COALESCE(SUM(n), 0) AS n FROM contatori WHERE chiave = ? AND giorno > ? AND giorno <= ?").bind(chiave, dal, al).first()) || { n: 0 }).n;
      return {
        installazioni: await uno("SELECT COUNT(DISTINCT installazione) AS n FROM eventi WHERE giorno > ? AND giorno <= ?"),
        sessioni: await uno("SELECT COUNT(*) AS n FROM eventi WHERE evento = 'sessione' AND giorno > ? AND giorno <= ?"),
        versioni: await colonna("versione"),
        sistemi: await colonna("sistema"),
        comandi: (await db.prepare(
          `SELECT valore, COUNT(*) AS n FROM eventi WHERE evento = 'comando' AND giorno > ? AND giorno <= ? AND ${VISTE}
           GROUP BY valore ORDER BY n DESC LIMIT 20`).bind(dal, al).all()).results,
        guardie: (await db.prepare(
          `SELECT valore, COUNT(*) AS n, COUNT(DISTINCT installazione) AS installazioni FROM eventi
           WHERE evento = 'guardia' AND giorno > ? AND giorno <= ? AND ${VISTE} GROUP BY valore ORDER BY n DESC LIMIT 20`)
          .bind(dal, al).all()).results,
        aggiorna: await gruppo("aggiorna"),
        config: await gruppo("config"),
        deriva: await this.deriva(dal, al, settimana),
        guardieFrequenti: settimana ? (await db.prepare(
          `SELECT installazione, valore, COUNT(*) AS n FROM eventi WHERE evento = 'guardia' AND giorno > ? AND giorno <= ? AND ${VISTE}
           GROUP BY installazione, valore HAVING n >= ? ORDER BY n DESC LIMIT 20`)
          .bind(dal, al, LIMITI.guardieFrequenti).all()).results : null,
        migliorare: settimana ? await this.miglioramento(al) : null,
        segnalazioni: await uno("SELECT COUNT(*) AS n FROM segnalazioni WHERE substr(ricevuta, 1, 10) > ? AND substr(ricevuta, 1, 10) <= ?"),
        scartati: await contatore("scartati"),
        telegramKo: await contatore("telegram-ko"),
        emailKo: await contatore("email-ko"),
      };
    },
    async pulisci(prima) {
      await db.batch([
        db.prepare("DELETE FROM eventi WHERE giorno < ?").bind(prima),
        db.prepare("DELETE FROM contatori WHERE giorno < ?").bind(prima),
        // Le chiavi "una volta per installazione" (giorno 'sempre', come setup-fine:<id>) non hanno una data:
        // se ne vanno con l'ultimo evento della loro installazione, cioè dopo gli stessi 12 mesi (#3507).
        db.prepare(`DELETE FROM contatori WHERE giorno = 'sempre' AND NOT EXISTS
          (SELECT 1 FROM eventi WHERE eventi.installazione = substr(contatori.chiave, instr(contatori.chiave, ':') + 1))`),
        // Il feedback del sito può avere un'email: si cancella con gli eventi, dopo 12 mesi.
        db.prepare("DELETE FROM feedback WHERE substr(ricevuto, 1, 10) < ?").bind(prima),
        // Le segnalazioni hanno testo libero e a volte l'id dell'installazione: dal 24/10/2026 se ne vanno anche
        // loro dopo 12 mesi, con la stessa data degli eventi. Prima restavano per sempre.
        db.prepare("DELETE FROM segnalazioni WHERE substr(ricevuta, 1, 10) < ?").bind(prima),
      ]);
    },
  };
}
