// Lancillotto sul server di Arturo (25/10/2026): gli eventi d'uso dell'app che annota come si lavora al Mac
// (repo stellakamikaze/lancillotto). Stanno in una tabella loro, eventi_lancillotto: i numeri di Arturo non
// si mescolano. Stesse regole di Arturo: id casuale, solo il giorno, elenco chiuso di eventi e di valori,
// mai testo, siti, titoli, nomi di app o di file. Il client è lancillotto/telemetria.py.

const unoDi = (voci) => new RegExp(`^(${voci.map((v) => v.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})$`);

// I browser da cui Lancillotto legge l'URL: lo stesso elenco di Esclusioni.browser nel registratore.
export const BROWSER = ["com.apple.Safari", "com.apple.SafariTechnologyPreview", "com.google.Chrome", "com.google.Chrome.canary",
  "company.thebrowser.Browser", "com.brave.Browser", "com.microsoft.edgemac", "org.mozilla.firefox", "org.chromium.Chromium",
  "com.vivaldi.Vivaldi", "com.operasoftware.Opera"];
export const SENSORI = ["app", "ax", "input", "schermo", "ocr", "testo", "file", "appunti", "avvio_login", "menu"];
export const VERBI = ["stato", "oggi", "giorno", "settimana", "routine", "episodi", "episodio", "catene", "cerca", "conta", "verifica",
  "testo", "conferma", "rifiuta", "automatizzata", "rivedi", "mostra", "raggiungo", "pausa", "riprendi", "escludi", "dimentica",
  "cancella-tutto", "telemetria"];

// L'elenco chiuso, uguale a EVENTI in lancillotto/telemetria.py (il test L03 li confronta).
// Le fasce (0-5) le calcola il client: il server non riceve mai un numero esatto di eventi, MB o ore.
export const EVENTI_LANCILLOTTO = {
  installa: /^(nuova|aggiorna|migrata)$/,
  guida: /^(benvenuto|accessibilita|testo|schermo|telemetria|fatto):(ok|saltato|si|no)$/,
  permesso: /^(ax|schermo):(si|no)$/,
  impostazione: /^(testo|valori|telemetria):(si|no)$/,
  giorno: /^(eventi|mb|ore):[0-5]$/,
  sensore: new RegExp(`^(${SENSORI.join("|")}):(guasto|degradato)$`),
  url_assente: unoDi(BROWSER),
  riavvio: /^[0-9]{1,3}$/,
  costo: /^(ocr|ax|cpu):[0-4]$/,
  finestra: /^(oggi|claude|privacy|arturo|guida)$/,
  comando: unoDi(VERBI),
  routine: /^(proposte:[0-9]{1,2}|confermata|rifiutata|automatizzata)$/,
  errore: /^(cli|registro|analisi|invio|permessi|avvio)$/,
};

const ID = /^[A-Za-z0-9-]{8,64}$/;
const GIORNO = /^\d{4}-\d{2}-\d{2}$/;
const VERSIONE = /^\d{1,3}\.\d{1,3}\.\d{1,3}$/;
const SISTEMA = /^macos-\d{2}$/;

const giorniFa = (giorno, n) => new Date(Date.parse(`${giorno}T12:00:00Z`) - n * 86400000).toISOString().slice(0, 10);

// Come validaLotto di Arturo: base sbagliata = 400 per il lotto intero, evento fuori elenco = scartato e contato.
export function validaLottoLancillotto(dati, giornoServer, { eventiPerLotto = 500, giorniIndietro = 7 } = {}) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const { installazione, versione, sistema, eventi } = dati;
  if (typeof installazione !== "string" || !ID.test(installazione)) return { motivo: "installazione non valida" };
  if (typeof versione !== "string" || !VERSIONE.test(versione)) return { motivo: "versione non valida" };
  if (typeof sistema !== "string" || !SISTEMA.test(sistema)) return { motivo: "sistema non valido" };
  if (!Array.isArray(eventi) || eventi.length === 0 || eventi.length > eventiPerLotto) return { motivo: "eventi mancanti o troppi" };
  const minimo = giorniFa(giornoServer, giorniIndietro);
  const righe = [];
  let scartati = 0;
  for (const e of eventi) {
    const regola = e && typeof e === "object" && typeof e.evento === "string" && Object.hasOwn(EVENTI_LANCILLOTTO, e.evento)
      ? EVENTI_LANCILLOTTO[e.evento] : null;
    const valore = regola ? (e.valore ?? "") : null;
    if (!regola || typeof valore !== "string" || !regola.test(valore)) {
      scartati++;
      continue;
    }
    const giorno = typeof e.giorno === "string" && GIORNO.test(e.giorno) && e.giorno <= giornoServer && e.giorno >= minimo
      ? e.giorno : giornoServer;
    righe.push({ giorno, installazione, versione, sistema, evento: e.evento, valore });
  }
  return { righe, scartati, installazione };
}

export function avvisoInstallazioneLancillotto(riga) {
  return `Lancillotto: nuova installazione ${riga.installazione.slice(0, 8)} (${riga.versione}, ${riga.sistema}).`;
}

// Il blocco "Dove migliorare Lancillotto" del riepilogo, in righe corte. r viene da archivio.riepilogoLancillotto.
export function testoLancillotto(r) {
  if (!r || !r.installazioni) return "";
  const elenco = (lista) => (lista || []).map((x) => `${x.valore} (${x.n})`).join(", ") || "nessuno";
  return [
    "Dove migliorare Lancillotto",
    `- Installazioni attive: ${r.installazioni}. Versioni: ${elenco(r.versioni)}.`,
    `- Guida: ${elenco(r.guida)}.`,
    `- Permessi mancanti: ${elenco(r.permessiMancanti)}.`,
    `- Sensori guasti o degradati: ${elenco(r.sensori)}.`,
    `- Browser senza URL: ${elenco(r.urlAssente)}.`,
    `- Errori: ${elenco(r.errori)}. Riavvii dopo un blocco: ${r.riavvii}.`,
    `- Routine: ${elenco(r.routine)}. Comandi di Claude: ${elenco(r.comandi)}.`,
  ].join("\n");
}
