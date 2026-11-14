// La logica del server di Arturo, senza Cloudflare dentro: validazione, tetti, email, riepilogo.
// worker.js la collega a D1 e all'invio email; test.mjs la prova con node e un archivio finto.
//
// Cosa riceve il server, e solo questo:
//   POST /v1/eventi        un lotto di eventi d'uso, con un id di installazione casuale
//   POST /v1/segnalazioni  una segnalazione di /segnala: dall'11/11/2026 Claude la scrive e la manda da solo, e dice
//                          alla persona cosa è partito; in modo manuale parte dopo che l'ha letta e approvata
//   POST /v1/feedback      il modulo di feedback del sito (/api/feedback): testo, tipo, email facoltativa.
//                          Dal 24/10/2026 il vocale non si accetta più
//   POST /v1/sito          un download dal sito (/api/sito): il comando copiato o il repository aperto
//   POST /v1/lancillotto/eventi  gli eventi d'uso di Lancillotto (25/10/2026), in una tabella loro (lancillotto.js)
// Cosa dà, solo a chi ha il token (secret RIEPILOGO_TOKEN):
//   GET  /v1/riepilogo     il riepilogo della settimana in JSON, con "Dove migliorare Arturo"
//   GET  /v1/segnalazioni  le ultime 50 segnalazioni, senza testo; /v1/segnalazioni/<n> una intera (27/10/2026)
//   GET  /v1/uso           chi usa Arturo, quanto e come: una riga per installazione, ultimi 30 giorni (2/11/2026)
//   POST /v1/contributi/<n> lo stato e la risposta di una segnalazione, scritti da chi mantiene Arturo (4/11/2026)
// Lo sportello (4/11/2026, #3925): chi segnala riceve col numero un codice, che il server tiene solo come hash.
// Col codice nell'header x-arturo-codice la persona legge lo stato e la risposta, aggiunge un seguito o la ritira:
//   GET  /v1/contributi/<n>          stato, risposta, versione con la correzione
//   POST /v1/contributi/<n>/seguito  un'aggiunta alla segnalazione (le informazioni che chi la mantiene ha chiesto)
//   POST /v1/contributi/<n>/ritira   titolo, testo, pacchetto e seguiti cancellati, resta il numero
// Un codice sbagliato e un numero inesistente danno lo stesso 404: il numero da solo non dice se esiste.
// L'IP non viene mai salvato. Gli eventi hanno il solo giorno, mai l'ora.
// Telegram ed email sono campanelli (24/10/2026): mai il testo né l'email di chi scrive. Una segnalazione porta
// numero, tipo, da dove arriva e il link alla pagina privata (27/10/2026), un feedback numero, tipo e origine.

import { validaLottoLancillotto, avvisoInstallazioneLancillotto, testoLancillotto } from "./lancillotto.js";
import { DATA_A_NUMERO } from "./versioni.js";
import { pagina, sezione, scheda, codice } from "./email.js";
import { recapGiorno, recapSettimana, righeGiorno } from "./recap.js";

// Le liste chiuse dei valori (24/10/2026). Prima guardia, chiede, confermata ed errore accettavano qualunque
// slug, e comando qualunque nome: un client modificato o un hook personale con un nome parlante
// ("hook-di-rossi") arrivava fino al riepilogo. Il Worker non legge file: i nomi sono copiati qui dal
// repository, e il banco TF03 (tests/test_telemetria_f1_2026_10_24.py) li confronta con il codice e con
// bin/telemetria.py. Un valore fuori lista si scarta e si conta.
// GUARDIE: gli hook che registrano guardia, chiede, confermata o errore. In hooks/bash-dispatcher.sh i nomi
// passati a run_guard; in hooks/web-egress-guard.py e hooks/protect_claude_md.py quelli passati a chiede() e
// a registra("errore").
export const GUARDIE = ["block-dangerous.py", "commit-secret-gate.py", "comms-guard.py", "data-guard.py", "exfil-guard.py",
  "gh-destructive-guard.py", "protect_claude_md.py", "web-egress-guard.py"];
// REGOLE: il suffisso .<regola> che bash-dispatcher.sh aggiunge al nome della guardia (riga "REGOLA:").
// block-dangerous: i nomi passati a _ask() in hooks/block-dangerous.py. commit-secret-gate: le famiglie del
// segreto, mai il nome del fornitore, e i tre casi senza segreto (_regola("scaduta"), _ask("repo-ignoto"),
// _ask("scansione-fallita")).
export const REGOLE = {
  "block-dangerous.py": ["avvio-automatico", "claude-md", "config", "docker-volumi", "find-delete", "git-clean", "rm-cartella",
    "rm-ignoto", "rm-illeggibile", "rm-protetto", "rm-xargs", "rmtree-cartella", "rmtree-illeggibile", "rmtree-variabile",
    "sblocco", "sblocco-claude-md", "sed-w", "sed-e", "segreto", "git-ramo", "git-stash", "git-destinazione", "git-amend", "git-worktree"],
  "commit-secret-gate.py": ["segreto-cloud", "segreto-token", "segreto-password", "segreto-chiave-privata", "segreto-altro",
    "scaduta", "repo-ignoto", "scansione-fallita"],
};
// COMANDI: i file di commands/, lo stesso elenco di COMANDI in bin/telemetria.py (banco M10). Il client manda
// "altro" per un comando che non è di Arturo: il server lo accetta, il nome vero non esce mai.
export const COMANDI = ["aggiorna", "creaskill", "diagnosi", "fine", "guidami", "inizio", "novita", "proponi", "segnala", "setup", "sparring"];
// SKILL: le cartelle di skills/, lo stesso elenco di SKILL in bin/telemetria.py (banco TS01, 3/11/2026). Come per i
// comandi, una skill della persona arriva come "altro".
export const SKILL = ["arturo", "concetti", "humanizer", "italiano-semplificato", "monitor", "prompt-master", "system-audit", "todo"];
// Le skill uscite (3/11/2026: i mod gws e riscrivi-bash, diventati hook; poi i sei mod diventati parti di skills/arturo):
// un client fino alla 0.2.x le manda ancora.
// Restano accettate perché un nome fuori elenco fa rifiutare il lotto intero; da togliere con l'evento tappa (#3435).
export const SKILL_USCITE = ["apri", "cache-fredda", "dafare", "gws", "redazione-segreti", "riscrivi-bash", "rotazione", "testata"];

// I nomi di Arturo che la deriva può dire oltre la forma (24/10/2026). La regex di `deriva` resta uguale, lettera per
// lettera, a quella del client (banco A01): la chiusura sta in derivaPubblica, come percorso_pubblico nel client.
// Un client di prima di F1, o uno modificato, mandava anche i file della persona (file:skills/clienti-rossi/SKILL.md,
// file:preventivo-rossi.md) e il recap li stampava. Qui sono chiusi i file della radice, le voci di skills/, agents/,
// commands/ e hooks/, dove la persona crea cose sue con nomi suoi, e gli hook di settings.json.
// Le altre radici (bin, docs, tests...) dal 8/11/2026 (review del 7/11, finding 37 e 38) escono come
// `file:<radice>/altro`: un clone senza upstream prendeva il repository della persona per Arturo, e
// file:docs/preventivo-clienti-rossi.md arrivava intero; un POST di chiunque metteva un testo suo nella nota di un task.
// Il banco TF05 (tests/test_telemetria_f1_2026_10_24.py) confronta questi elenchi col repository.
export const DERIVA_NOMI = {
  radice: [".gitattributes", ".gitignore", "LICENSE", "NOVITA.md", "PRODUCT.md", "README.md", "ROADMAP.md", "SECURITY.md", "package.json", "settings.json"],
  skills: ["arturo", "concetti", "humanizer", "italiano-semplificato", "monitor", "prompt-master", "system-audit", "todo"],
  agents: ["architecture-reviewer.md", "bug-finder.md", "fact-checker.md", "performance-profiler.md", "researcher.md",
    "structural-completeness-reviewer.md", "test-runner.md", "ui-ux-consultant.md"],
  commands: COMANDI.map((c) => `${c}.md`),
  hooks: ["agente-worktree.py", "bash-dispatcher.sh", "block-dangerous.py", "bozze-mcp-auto-approve.py", "commit-secret-gate.py", "comms-guard.py",
    "comms-prefilter.py", "context-monitor.js", "controlla-config.py", "credential-leak-scanner.py", "data-guard.py", "deriva.py", "emoji_remover.py",
    "exfil-guard.py", "fiducia.py", "forma_comando.py", "gh-destructive-guard.py", "gws-esito.py", "gws-token-health.py", "heredoc.py", "inject-now.sh",
    "input-notifier-start.sh", "melchior-postwrite.py", "melchior_match.py", "memory-autoload.py", "memory-retrieve.py", "memory-write-scanner.py",
    "metodo.sh", "prompt-injection-scanner.py", "protect_claude_md.py", "radici.py", "scheda-terminale.py", "session-end.sh", "session-start.sh",
    "statusline.js", "subagent-memory-context.py", "typecheck-after-edit.py", "web-egress-guard.py"],
};
// Gli hook che il settings.json di Arturo dichiara (hook_dichiarati in hooks/deriva.py), più "tutti" per disableAllHooks.
export const DERIVA_HOOK = ["agente-worktree.py", "bash-dispatcher.sh", "block-dangerous.py", "bozze-mcp-auto-approve.py", "context-monitor.js", "credential-leak-scanner.py",
  "emoji_remover.py", "gws-esito.py", "gws-token-health.py", "inject-now.sh", "input-notifier-start.sh", "melchior-postwrite.py", "memory-retrieve.py",
  "memory-write-scanner.py", "prompt-injection-scanner.py", "protect_claude_md.py", "scheda-terminale.py", "session-end.sh",
  "session-start.sh", "subagent-memory-context.py", "typecheck-after-edit.py", "web-egress-guard.py"];

// Il valore della deriva che si salva: un nome fuori elenco diventa `file:altro` o `hook:altro`, come nel client. Non si
// scarta: l'elenco corrente di un'installazione (le righe dopo `insieme:<n>`) resta intero, e il recap dice che c'era.
export function derivaPubblica(valore) {
  if (valore.startsWith("hook:")) return DERIVA_HOOK.includes(valore.slice(5)) || valore === "hook:tutti" ? valore : "hook:altro";
  if (!valore.startsWith("file:")) return valore;
  const [radice, nome, ...resto] = valore.slice(5).split("/");
  if (nome === undefined) return radice === "altro" || DERIVA_NOMI.radice.includes(radice) ? valore : "file:altro";
  if (radice === "radice") return "file:altro";
  if (!Object.hasOwn(DERIVA_NOMI, radice)) return `file:${radice}/altro`;
  return DERIVA_NOMI[radice].includes(nome) && (radice !== "skills" || resto.length) ? valore : "file:altro";
}

// Il valore della deriva come lo dicono la nota di un task e il recap: solo nomi degli elenchi chiusi. Di una skill
// di Arturo resta il nome della skill, senza il percorso dentro (review del 7/11, finding 37).
export function derivaInBreve(valore) {
  const v = derivaPubblica(valore);
  if (v.startsWith("hook:")) return v.slice(5);
  if (!v.startsWith("file:")) return "altro";
  const [radice, nome] = v.slice(5).split("/");
  return nome === undefined ? radice : `${radice}/${nome}`;
}

// La versione che si salva: il rilascio di Arturo (rilascio()), senza il conteggio e l'hash dei commit della persona, oppure
// "sconosciuta" (24/10/2026). Prima passava ogni testo con la forma di VERSIONE: un tag della persona come "v-clienti-rossi"
// arrivava nel D1, negli avvisi su Telegram, nell'email della config rotta e in "Versioni in uso". Una versione senza la
// forma di VERSIONE resta un lotto malformato (400).
export function versionePubblica(versione) {
  return rilascio(versione) || "sconosciuta";
}

const esatto = (v) => v.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const unoDi = (valori) => new RegExp(`^(${valori.map(esatto).join("|")})$`);
const GUARDIA_E_REGOLA = unoDi([...GUARDIE, ...Object.entries(REGOLE).flatMap(([g, regole]) => regole.map((r) => `${g}.${r}`))]);

// L'elenco chiuso degli eventi. Lo stesso elenco sta in bin/telemetria.py e nel README:
// il banco M09 controlla che coincidano, salvo gli eventi vecchi che il client non manda più.
export const EVENTI = {
  // Dal 14/11/2026 la forma dell'installazione: plugin o clone (vuoto da una versione di prima).
  sessione: /^(|plugin|clone)$/,
  comando: unoDi([...COMANDI, "altro"]),
  guardia: GUARDIA_E_REGOLA,
  aggiorna: /^(applicato|conflitto|fallito|rifiutato|indietro|scartato|automatico|rinviato|bloccato-firma|bloccato-verifica|bloccato-storia|bloccato-versione|manuale|bloccato-modifiche|bloccato-attesa|non-partito)$/,
  segnalazione: /^(problema|proposta|integrazione)$/,
  // La distanza fra la config della persona e quella di Arturo: un `insieme:<n>` apre l'elenco
  // corrente, seguito da n righe. Dei file esce solo il percorso dentro Arturo, che è pubblico.
  // Il percorso è relativo, senza "..", e comincia da una radice di Arturo o è un file della radice.
  deriva: /^(insieme:\d{1,3}|hook:[a-z0-9_.-]{1,60}|file:(?!.*\.\.)((agents|bin|commands|docs|firme|hooks|output-styles|server|shared|skills|templates|tests|tools|\.github)\/[A-Za-z0-9_.\/-]{1,70}|[A-Za-z0-9_.-]{1,40}))$/,
  config: /^rotta-(settings|conflitto|rebase|hook)$/,
  // Dal 15/10/2026, per il miglioramento di Arturo. In coda, nello stesso ordine di bin/telemetria.py.
  setup: /^(fase:(10|[0-9][a-z]?)|fine)$/,
  chiede: GUARDIA_E_REGOLA,
  confermata: GUARDIA_E_REGOLA,
  errore: GUARDIA_E_REGOLA,
  claude: /^\d{1,3}\.\d{1,3}\.\d{1,4}$/,
  // Dal 3/11/2026 (#4540): alla chiusura della sessione la durata e i messaggi della persona in fasce, e le skill usate.
  durata: /^(<5m|5-30m|30m-2h|>2h)$/,
  turni: /^(1|2-5|6-20|>20)$/,
  skill: unoDi([...SKILL, ...SKILL_USCITE, "altro"]),
  // Dal 3/11/2026: un banco delle guardie diventato rosso su un computer (tests/banchi-avvio.sh).
  banchi: /^test[a-z0-9_-]{1,56}\.py$/,
  // Eventi vecchi: il client non li manda più, ma un client non aggiornato sì. Restano accettati per
  // non perdere i dati dei client fermi (prima del 24/10/2026 un evento fuori elenco faceva rifiutare il
  // lotto intero). Da togliere dopo qualche settimana, insieme al loro posto in M09 (tests/test_telemetria.py).
  // tappa: tolta dal client il 16/10/2026 con il percorso a tappe. Per la stessa ragione `deriva`
  // accetta ancora la radice templates/, tolta dal client il 16/10/2026: esce con tappa (#3435).
  tappa: /^(tappa:[0-4]|(decisioni|limiti|tenuti|proposte|rifiutate):\d{1,4})$/,
};
// Le soglie della ritenzione: installazioni ancora vive dopo 7, 30 e 60 giorni dalla prima volta.
// Sessanta giorni è il criterio di successo di Arturo (uso vivo dopo due mesi).
export const RITENZIONE = [7, 30, 60];
export const TIPI = ["problema", "proposta", "integrazione"];
// Lo sportello (4/11/2026, #3925). Gli stati che chi mantiene Arturo assegna, più "ritirata", che assegna solo la
// persona col suo codice. Le voci del pacchetto tecnico sono le caselle dell'anteprima di /segnala (bin/segnala.py,
// VOCI_PACCHETTO): la voce "collega" non viaggia nel pacchetto, diventa l'id dell'installazione.
export const STATI = ["ricevuta", "serve-info", "in-lavoro", "chiusa", "rifiutata"];
export const VOCI_PACCHETTO = ["ambiente", "banchi", "config", "deriva", "errore"];
export const ORIGINI = ["segnala", "avvio", "fine"];
export const SISTEMI = ["Darwin", "Linux", "Windows", "altro"];
export const LIMITI = {
  corpoEventi: 64 * 1024,
  // Dal 4/11/2026 il corpo porta anche il pacchetto tecnico: 16000 caratteri di testo più cinque voci da 4000.
  corpoSegnalazione: 48 * 1024,
  vocePacchetto: 4000,
  risposta: 4000,
  seguito: 8000,
  seguitiPerSegnalazione: 10,
  // Il pacchetto tecnico si svuota prima del testo: serve alla diagnosi, non alla storia.
  pacchettoGiorni: 90,
  eventiPerLotto: 500,
  eventiPerGiorno: 500,
  eventiTotaliPerGiorno: 100000,
  // Le installazioni nuove accettate in un giorno (8/11/2026, review del 7/11, finding 40): il tetto per installazione
  // si aggirava con un id nuovo a ogni POST, e da un solo IP 200 lotti riempivano il server per il giorno.
  installazioniNuovePerGiorno: 50,
  // La deriva (finding 37 e 41): al massimo tanti task per email, il resto in una riga; al massimo tante installazioni
  // lette, prima quelle viste in più giorni.
  taskDerivaPerEmail: 10,
  derivaInstallazioni: 100,
  segnalazioniPerGiorno: 200,
  segnalazioniInElenco: 50,
  // Il contatto di chi segnala (10/11/2026): il nome come lo scrive la persona, l'email col tetto del feedback.
  contattoNome: 80,
  contattoEmail: 200,
  // Due tetti separati (16/10/2026): le segnalazioni, che chiunque può mandare, non consumano le
  // email delle config rotte.
  emailRottePerGiorno: 20,
  emailSegnalazioniPerGiorno: 20,
  // Gli avvisi su Telegram che un POST senza autenticazione può far partire: oltre il tetto il dato si salva, il
  // messaggio no (review di sicurezza del 16/10/2026).
  avvisiInstallazioniPerGiorno: 20,
  avvisiSetupPerGiorno: 20,
  avvisiSegnalazioniPerGiorno: 30,
  // Una data dichiarata dal client più vecchia di così diventa il giorno del server.
  giorniIndietro: 7,
  guardieFrequenti: 5,
  // Le statistiche delle guardie contano solo installazioni viste in almeno tanti giorni diversi (#3507).
  giorniGuardie: 2,
  conservazioneGiorni: 365,
  // Il sito (16/10/2026): il modulo di feedback e i download. Il vocale non si accetta più dal 24/10/2026, e
  // dal 25/10/2026 il tetto del corpo è quello di un messaggio scritto (Federico: "voglio solo messaggi
  // scritti"): 4000 caratteri ed email stanno larghi in 64 KB, un vocale vero non entra e torna 413.
  feedbackPerGiorno: 100,
  feedbackTesto: 4000,
  feedbackCorpo: 64 * 1024,
  sitoPerGiorno: 60,
  // Installazioni rimaste indietro (23/10/2026): attive negli ultimi `fermaGiorni` giorni, senza un rilascio
  // uscito da almeno altrettanti. Su Telegram al massimo una volta ogni `avvisoIndietroOgni` giorni per
  // installazione, e non più di `avvisiIndietroPerGiorno` al giorno.
  fermaGiorni: 3,
  avvisoIndietroOgni: 7,
  avvisiIndietroPerGiorno: 5,
};

const FEEDBACK_TIPI = ["problema", "idea", "installazione", "altro"];
const SITO_TIPI = ["download", "github"];
const SITO_SISTEMI = ["mac", "win", ""];

const ID = /^[A-Za-z0-9-]{8,64}$/;
const CODICE = /^[0-9a-f]{32}$/;
const GIORNO = /^\d{4}-\d{2}-\d{2}$/;
// La versione è l'ultimo tag di rilascio raggiungibile (`git describe --tags --abbrev=0`, bin/telemetria.py), oppure
// "sconosciuta". Niente testo libero: finisce nel riepilogo che legge la routine del lunedì. Si salva solo il rilascio
// (versionePubblica).
const VERSIONE = /^[A-Za-z0-9._+-]{1,60}$/;

export function oggi(adesso = new Date()) {
  return adesso.toISOString().slice(0, 10);
}

const giornoMeno = (giorno, n) => oggi(new Date(Date.parse(`${giorno}T00:00:00Z`) - n * 86400000));

// Il rilascio di una versione, senza i commit della persona: "v0.2.0-1-gdf1c2d0" -> "v0.2.0". Dal 3/11/2026 la versione
// è un numero. Una copia installata prima manda ancora la data del rilascio ("v2026-10-19.2"), e qui diventa il suo
// numero (versioni.js). Una data che non è stata un rilascio, o una versione senza rilascio (sconosciuta, un ramo di
// prova), dà null.
export function rilascio(versione) {
  const m = /^(v\d{1,4}\.\d{1,4}\.\d{1,6}|v\d{4}-\d{2}-\d{2}(?:\.\d+)?)(?:-\d+-g[0-9a-f]+)?$/.exec(versione || "");
  if (!m) return null;
  return m[1].includes("-") ? DATA_A_NUMERO[m[1]] || null : m[1];
}

export function confronta(a, b) {
  const x = a.slice(1).split(".").map(Number);
  const y = b.slice(1).split(".").map(Number);
  return x[0] - y[0] || x[1] - y[1] || x[2] - y[2];
}

const NOTI = new Set(Object.values(DATA_A_NUMERO));

// Le installazioni rimaste indietro (23/10/2026). Un'installazione è restata quattro giorni alla v2026-10-19.2, che
// rinviava l'aggiornamento automatico con Chrome aperto, e un'altra prima di lei alla v2026-10-15.2: un
// difetto dell'aggiornamento impedisce l'aggiornamento che lo corregge, e solo un /aggiorna a mano lo sblocca.
// `attive`: {installazione, versione, ultima} con la versione dell'ultimo evento. `versioni`: {versione, prima},
// il primo giorno in cui il server l'ha vista, e `n`, quante installazioni l'hanno mandata. Un rilascio conta se è
// uscito da almeno `fermaGiorni` giorni e se è vero: un rilascio a data della tabella, oppure un numero mandato da
// almeno due installazioni. Così una versione inventata da un lotto non fa sembrare indietro tutti.
export function calcolaIndietro(attive, versioni, al, giorni = LIMITI.fermaGiorni) {
  const soglia = giornoMeno(al, giorni);
  const uscita = new Map();
  const viste = new Map();
  for (const v of versioni) {
    const r = rilascio(v.versione);
    if (!r) continue;
    viste.set(r, (viste.get(r) || 0) + (Number(v.n) || 0));
    if (!uscita.has(r) || v.prima < uscita.get(r)) uscita.set(r, v.prima);
  }
  for (const r of [...uscita.keys()]) if (!NOTI.has(r) && viste.get(r) < 2) uscita.delete(r);
  const maturi = [...uscita].filter(([, prima]) => prima <= soglia).map(([r]) => r).sort(confronta);
  const fuori = [];
  for (const a of attive) {
    const r = rilascio(a.versione);
    if (!r) continue;
    const mancanti = maturi.filter((m) => confronta(m, r) > 0);
    if (!mancanti.length) continue;
    fuori.push({ installazione: a.installazione, rilascio: r, ultima: a.ultima, nuovo: mancanti[mancanti.length - 1],
      dal: uscita.get(mancanti[0]) });
  }
  return fuori.sort((x, y) => (x.dal < y.dal ? -1 : x.dal > y.dal ? 1 : 0));
}

function risposta(status, dati) {
  return new Response(JSON.stringify(dati), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

async function leggiJson(request, limite) {
  const testo = await request.text();
  if (new TextEncoder().encode(testo).length > limite) return { errore: risposta(413, { errore: "troppo grande" }) };
  try {
    return { dati: JSON.parse(testo) };
  } catch {
    return { errore: risposta(400, { errore: "JSON non valido" }) };
  }
}

function testoCorto(valore, massimo) {
  return typeof valore === "string" && valore.length <= massimo ? valore : null;
}

// Le righe valide di un lotto e quante se ne scartano, oppure il motivo per cui il lotto intero non vale.
// Dal 24/10/2026 il lotto passa in parte: un evento fuori elenco si scarta e si conta, gli altri si salvano.
// Prima un solo evento ignoto faceva rispondere 400, e il client toglieva dalla coda anche gli eventi buoni.
// Il motivo resta per il lotto malformato: base mancante o storta, eventi che non sono un elenco.
export function validaLotto(dati, giornoServer) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const { installazione, versione, sistema, eventi } = dati;
  if (typeof installazione !== "string" || !ID.test(installazione)) return { motivo: "installazione non valida" };
  if (typeof versione !== "string" || !VERSIONE.test(versione)) return { motivo: "versione non valida" };
  const pubblica = versionePubblica(versione);
  if (!SISTEMI.includes(sistema)) return { motivo: "sistema non valido" };
  if (!Array.isArray(eventi) || eventi.length === 0 || eventi.length > LIMITI.eventiPerLotto) return { motivo: "eventi mancanti o troppi" };
  const righe = [];
  let scartati = 0;
  const minimo = giorniFa(new Date(`${giornoServer}T12:00:00Z`), LIMITI.giorniIndietro);
  for (const e of eventi) {
    // Solo le chiavi proprie di EVENTI: "constructor" o "__proto__" non sono eventi.
    const regola = e && typeof e === "object" && typeof e.evento === "string" && Object.hasOwn(EVENTI, e.evento) ? EVENTI[e.evento] : null;
    const valore = regola ? (e.valore ?? "") : null;
    if (!regola || typeof valore !== "string" || !regola.test(valore)) {
      scartati++;
      continue;
    }
    // Un giorno nel futuro, troppo vecchio o malformato diventa il giorno del server.
    const giorno = typeof e.giorno === "string" && GIORNO.test(e.giorno) && e.giorno <= giornoServer && e.giorno >= minimo
      ? e.giorno : giornoServer;
    righe.push({ giorno, installazione, versione: pubblica, sistema, evento: e.evento,
      valore: e.evento === "deriva" ? derivaPubblica(valore) : valore });
  }
  return { righe, scartati, installazione };
}

// Il contatto di chi segnala (10/11/2026): nome ed email che la persona ha dato una volta con `arturo contatto`,
// per essere ricontattata sulle sue segnalazioni. Facoltativo. Un contatto malformato non ferma la segnalazione:
// si scarta, e la risposta lo dice. Non va mai nei campanelli, nel recap o nella telemetria (R18, V60).
export const RE_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export function validaContatto(c) {
  if (c === undefined || c === null) return { contatto: null };
  if (typeof c !== "object" || Array.isArray(c)) return { contatto: null, scartato: true };
  const nome = typeof c.nome === "string" ? c.nome.trim() : "";
  const email = typeof c.email === "string" ? c.email.trim() : "";
  if (!nome && !email) return { contatto: null };
  if (nome.length > LIMITI.contattoNome || /[\u0000-\u001f\u007f]/.test(nome)) return { contatto: null, scartato: true };
  if (!email || email.length > LIMITI.contattoEmail || !RE_EMAIL.test(email)) return { contatto: null, scartato: true };
  return { contatto: { nome, email } };
}

export function validaSegnalazione(dati) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const tipo = TIPI.includes(dati.tipo) ? dati.tipo : null;
  const titolo = testoCorto(dati.titolo, 200);
  const testo = testoCorto(dati.testo, 16000);
  if (!tipo || !titolo || !titolo.trim() || !testo || !testo.trim()) return { motivo: "tipo, titolo o testo non validi" };
  const installazione = typeof dati.installazione === "string" && ID.test(dati.installazione) ? dati.installazione : "";
  // Il pacchetto tecnico (4/11/2026): solo le voci dell'elenco chiuso, ognuna testo corto. Una voce fuori elenco o
  // troppo lunga si lascia fuori, senza rifiutare la segnalazione: il testo che la persona ha approvato arriva.
  const pacchetto = {};
  if (dati.pacchetto && typeof dati.pacchetto === "object" && !Array.isArray(dati.pacchetto)) {
    for (const voce of VOCI_PACCHETTO) {
      const valore = testoCorto(dati.pacchetto[voce], LIMITI.vocePacchetto);
      if (valore && valore.trim()) pacchetto[voce] = valore;
    }
  }
  const { contatto, scartato } = validaContatto(dati.contatto);
  return {
    contatto: contatto ? "salvato" : scartato ? "scartato" : "",
    segnalazione: {
      tipo,
      titolo: titolo.trim(),
      testo,
      versione: typeof dati.versione === "string" && VERSIONE.test(dati.versione) ? versionePubblica(dati.versione) : "",
      sistema: SISTEMI.includes(dati.sistema) ? dati.sistema : "altro",
      installazione,
      origine: ORIGINI.includes(dati.origine) ? dati.origine : "segnala",
      pacchetto: Object.keys(pacchetto).length ? JSON.stringify(pacchetto) : "",
      contatto_nome: contatto ? contatto.nome : "",
      contatto_email: contatto ? contatto.email : "",
    },
  };
}

// Il codice della ricevuta: 128 bit casuali in esadecimale. Sul server resta solo lo SHA-256.
export function nuovoCodice() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) => b.toString(16).padStart(2, "0")).join("");
}

export async function hashCodice(codice) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(codice));
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

// Quello che la persona legge col suo codice: mai titolo, testo o pacchetto, che ha già nella sua copia.
export function vistaPersona(riga) {
  let seguiti = 0;
  try {
    seguiti = (JSON.parse(riga.seguiti || "[]") || []).length;
  } catch {
    seguiti = 0;
  }
  return { numero: riga.id, stato: riga.stato || "ricevuta", risposta: riga.risposta || "",
    versione_fix: riga.versione_fix || "", aggiornata: riga.aggiornata || "", seguiti };
}

export function validaRisposta(dati) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const cambi = {};
  if (dati.stato !== undefined) {
    if (!STATI.includes(dati.stato)) return { motivo: `stato fuori elenco (${STATI.join(", ")})` };
    cambi.stato = dati.stato;
  }
  if (dati.risposta !== undefined) {
    const r = testoCorto(dati.risposta, LIMITI.risposta);
    if (r === null) return { motivo: `risposta oltre ${LIMITI.risposta} caratteri` };
    cambi.risposta = r;
  }
  if (dati.versione_fix !== undefined) {
    if (typeof dati.versione_fix !== "string" || !(dati.versione_fix === "" || VERSIONE.test(dati.versione_fix))) {
      return { motivo: "versione_fix non valida" };
    }
    cambi.versione_fix = dati.versione_fix;
  }
  if (!Object.keys(cambi).length) return { motivo: "niente da cambiare: stato, risposta o versione_fix" };
  return { cambi };
}

// --- email -------------------------------------------------------------------

function base64(testo) {
  const byte = new TextEncoder().encode(testo);
  let binario = "";
  for (const b of byte) binario += String.fromCharCode(b);
  return btoa(binario).replace(/.{76}/g, "$&\r\n");
}

function intestazione(testo) {
  // RFC 2047: un oggetto con accenti passa intatto.
  return /^[\x20-\x7e]*$/.test(testo) ? testo : `=?UTF-8?B?${btoa(String.fromCharCode(...new TextEncoder().encode(testo)))}?=`;
}

// Dal 5/11/2026 con `html` l'email è multipart/alternative: il testo semplice resta per chi non legge l'HTML.
// `intestazioni` sono righe in più per la testa (l'header del task): una riga che porta un a capo si scarta, perché
// aprirebbe un header o un corpo nuovo.
export function mime({ da, a, oggetto, testo, html = "", intestazioni = [], adesso = new Date(), id = crypto.randomUUID() }) {
  const dominio = da.split("@")[1];
  const testa = [
    `From: Arturo <${da}>`,
    `To: ${a}`,
    `Subject: ${intestazione(oggetto.replace(/[\r\n]+/g, " "))}`,
    `Date: ${adesso.toUTCString()}`,
    `Message-ID: <${id}@${dominio}>`,
    ...intestazioni.filter((r) => typeof r === "string" && new RegExp(`^[A-Za-z0-9-]{1,40}: [\\x21-\\x7e]{1,${HEADER_MASSIMO}}$`).test(r)),
    "MIME-Version: 1.0",
  ];
  const parte = (tipo, corpo) => [`Content-Type: ${tipo}; charset=utf-8`, "Content-Transfer-Encoding: base64", "", base64(corpo)];
  if (!html) return [...testa, ...parte("text/plain", testo)].join("\r\n");
  const confine = `arturo-${id.replace(/[^A-Za-z0-9]/g, "")}`;
  return [...testa, `Content-Type: multipart/alternative; boundary="${confine}"`, "",
    `--${confine}`, ...parte("text/plain", testo), `--${confine}`, ...parte("text/html", html), `--${confine}--`, ""].join("\r\n");
}

// Il task che viaggia nell'email (5/11/2026). Chi mantiene Arturo può far leggere la casella a un programma che
// trasforma l'header in un task del suo tracker: la segnalazione, la config rotta e le righe "da fare" del recap
// arrivano già come cose da fare. Il valore è un JSON in base64url con fp (l'impronta stabile, che evita i doppioni),
// progetto, prio, titolo, note e chi. Il nome dell'header e il progetto vengono dalle variabili del Worker
// INTESTAZIONE_TASK e TASK_PROGETTO: senza, l'email parte senza header. Titolo e note li scrive il server, mai il
// testo di chi segnala.
export function task(id, titolo, { prio = "med", chi = "Claude", note = "" } = {}) {
  return { fp: `auto:arturo:${String(id).replace(/[^A-Za-z0-9._:-]/g, "-").slice(0, 80)}`, prio, chi, titolo: titolo.slice(0, 80),
    ...(note ? { note: note.slice(0, 600) } : {}) };
}

// Il valore dell'header sta entro HEADER_MASSIMO caratteri, il tetto che mime() accetta. Una nota più lunga si accorcia
// finché il base64 ci sta (8/11/2026, finding 45): prima l'header di una deriva di venti file cadeva in silenzio, mentre il
// recap diceva "ogni riga è già un task". Gli accenti pesano due byte, quindi il taglio si misura sul valore codificato.
export const HEADER_MASSIMO = 900;
export function intestazioneTask(nome, progetto, t) {
  if (!nome || !progetto || !/^[A-Za-z0-9-]{1,40}$/.test(nome)) return null;
  const codifica = (x) => {
    let binario = "";
    for (const b of new TextEncoder().encode(JSON.stringify({ ...x, progetto }))) binario += String.fromCharCode(b);
    return btoa(binario).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  };
  let x = { ...t };
  let valore = codifica(x);
  while (valore.length > HEADER_MASSIMO && x.note) {
    const note = x.note.length > 40 ? `${x.note.slice(0, x.note.length - 40).trimEnd()}…` : "";
    x = note ? { ...x, note } : (({ note: _, ...resto }) => resto)(x);
    valore = codifica(x);
  }
  return valore.length <= HEADER_MASSIMO ? `${nome}: ${valore}` : null;
}

// Chi è un'installazione nelle email e nei task: le prime 8 cifre dell'id. Dal 8/11/2026 (review del 7/11, finding 39)
// il Worker non conosce più i nomi delle persone: dal 5/11 il secret NOMI_INSTALLAZIONI li legava all'id, e
// docs/privacy.md promette che quei nomi stanno solo sul server privato di chi mantiene Arturo.
export const idCorto = (installazione) => (installazione || "").slice(0, 8) || "senza id";

// Il tipo in parole, per chi legge l'avviso (27/10/2026): "proposta" da sola non diceva che è un'idea.
const TIPO_IN_PAROLE = { problema: "un problema", proposta: "un'idea", integrazione: "un'integrazione" };

// Chi ha segnalato, nella forma che esce dal server: 8 caratteri dell'installazione, la versione, il sistema.
function provenienza(s) {
  const parti = [s.installazione ? `installazione ${s.installazione.slice(0, 8)}` : "installazione senza id",
    s.versione ? `Arturo ${s.versione}` : "", s.sistema || "", s.contatto_email ? "con contatto" : ""];
  return parti.filter(Boolean).join(" · ");
}

// Il link alla pagina che mostra la segnalazione intera, dietro il login di chi mantiene Arturo (27/10/2026).
// La base arriva dalla variabile LEGGI_SEGNALAZIONI del Worker: senza, l'avviso dice di leggerla col token.
const linkSegnalazione = (leggi, numero) => (leggi ? `${leggi.replace(/\/+$/, "")}/${Number(numero)}` : "");

// L'ora di arrivo in ora di Roma, "27/10 alle 15:52".
function oraRoma(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const p = Object.fromEntries(new Intl.DateTimeFormat("it-IT", { timeZone: "Europe/Rome", day: "2-digit", month: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d).map((x) => [x.type, x.value]));
  return `${p.day}/${p.month} alle ${p.hour}:${p.minute}`;
}

// L'email di una segnalazione è un campanello (24/10/2026): niente titolo né testo. Prima portava il titolo, il
// testo intero e l'id completo dell'installazione, e ogni copia restava nella casella di chi mantiene Arturo,
// fuori dalla pulizia dei 12 mesi e da ogni cancellazione. Dal 27/10/2026 il campanello si legge senza comandi:
// tipo in parole, da dove arriva, l'ora e il link alla pagina che mostra il testo.
// Dal 5/11/2026 anche in HTML, con il task: "Leggere la segnalazione n. N", un'idea a priorità bassa.
export function emailSegnalazione(s, numero, { leggi = "", ricevuta = "" } = {}) {
  const n = Number(numero);
  const link = linkSegnalazione(leggi, n);
  const quando = oraRoma(ricevuta);
  const tipo = TIPO_IN_PAROLE[s.tipo] || s.tipo;
  const chi = s.installazione ? idCorto(s.installazione) : "installazione senza id";
  const html = pagina({
    testa: `Arturo · segnalazione${quando ? ` · ${quando}` : ""}`,
    titolo: `È arrivata la segnalazione n. ${n}: ${tipo}`,
    blocchi: [sezione("Da dove arriva", scheda([["Tipo", tipo], ["Da", chi],
      ["Versione", s.versione || "non detta"], ["Sistema", s.sistema || "altro"], ["Origine", `/${s.origine || "segnala"}`],
      ...(quando ? [["Arrivata", quando]] : [])]))],
    azione: link ? { href: link, etichetta: "Leggi la segnalazione" } : null,
    piede: [link ? "La pagina chiede il tuo accesso." : `Si legge con GET /v1/segnalazioni/${n} e il token del riepilogo.`,
      "Il testo resta sul server e non passa da questa email.", "Arriva a chi mantiene Arturo, una per segnalazione."],
  });
  return {
    oggetto: `[Arturo] Segnalazione n. ${n}: ${tipo}`,
    testo: `È arrivata la segnalazione n. ${n} su Arturo.\n\n` +
      `Tipo: ${tipo}\nDa: ${provenienza(s)}\n` +
      (quando ? `Arrivata: ${quando}\n` : "") +
      (link ? `\nLeggila qui, col tuo accesso:\n${link}\n` : `\nSi legge con GET /v1/segnalazioni/${n} e il token del riepilogo.\n`) +
      `\nIl testo resta sul server e non passa da questa email.\n`,
    html,
    task: [task(`segnalazione:${n}`, `Leggere la segnalazione n. ${n} di Arturo (${s.tipo})`, {
      prio: s.tipo === "problema" ? "med" : "low",
      note: link ? `Leggi la segnalazione e rispondi dallo sportello: [segnalazione n. ${n}](${link})` : `GET /v1/segnalazioni/${n} col token del riepilogo.`,
    })],
  };
}

const ROTTA_IN_PAROLE = { settings: "settings.json non si legge", conflitto: "un conflitto di merge nella config",
  rebase: "un rebase lasciato a metà", hook: "un hook di Arturo che manca" };

export function emailConfigRotta(installazione, valore, versione, { adesso = new Date() } = {}) {
  const tipo = valore.replace("rotta-", "");
  const chi = idCorto(installazione);
  const html = pagina({
    testa: `Arturo · config rotta · ${oraRoma(adesso.toISOString())}`,
    titolo: `La config di ${chi} è rotta: le guardie possono non girare`,
    blocchi: [sezione("Cosa si sa", scheda([["Installazione", codice(chi)],
      ["Guasto", ROTTA_IN_PAROLE[tipo] || tipo], ["Versione", `Arturo ${versione}`]]))],
    piede: ["Una sola email al giorno per installazione.", "Il recap di domattina la riporta fra le cose da fare."],
  });
  return {
    oggetto: "[Arturo] Config rotta su un'installazione",
    testo: `Un'installazione di Arturo ha la config rotta (${tipo}): le guardie possono non girare.\n\n` +
      `Installazione ${installazione.slice(0, 8)} · Arturo ${versione}\n`,
    html,
    task: [taskRotta(installazione, tipo, oggi(adesso))],
  };
}

// Una config rotta fa un task al mese per installazione e guasto: se resta rotta per giorni, non nasce un task al giorno.
export const taskRotta = (installazione, tipo, giorno) =>
  task(`rotta:${corto(installazione)}:${tipo}:${giorno.slice(0, 7)}`, `Riparare la config rotta di ${idCorto(installazione)} (${tipo})`,
    { note: `Guasto: ${ROTTA_IN_PAROLE[tipo] || tipo}. Il primo passo è chiedere a chi la usa l'output di /diagnosi.` });

const corto = (id) => id.slice(0, 8);
const giorni = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 86400000);

// Da {installazione, prima, ultima} ai numeri della ritenzione. Per ogni soglia contano solo le
// installazioni nate da almeno quei giorni: una nata ieri non può essere viva a 30 giorni.
// Dal 24/10/2026 anche la ritenzione ha la finestra di 30 giorni del blocco "Dove migliorare": per la soglia n
// contano le installazioni nate fra n e n+30 giorni fa. Prima contava tutto lo storico, e le prime
// installazioni di prova pesavano per sempre sul numero.
export const FINESTRA = 30;
export function ritenzione(righe, al) {
  const fuori = { nuove: righe.filter((x) => giorni(x.prima, al) < 7).length, soglie: [] };
  for (const n of RITENZIONE) {
    const idonee = righe.filter((x) => giorni(x.prima, al) >= n && giorni(x.prima, al) < n + FINESTRA);
    fuori.soglie.push({ giorni: n, idonee: idonee.length, vive: idonee.filter((x) => giorni(x.prima, x.ultima) >= n).length });
  }
  return fuori;
}

// Viaggia col riepilogo in JSON: la routine che propone correzioni la legge insieme ai numeri (#3507).
export const REGOLA_GUARDIE = "Una guardia non si allenta sulla sola base della telemetria: gli id sono casuali e " +
  "chiunque può crearne. Le statistiche delle guardie contano solo installazioni viste in almeno " +
  `${LIMITI.giorniGuardie} giorni diversi, e ogni numero dice quante installazioni lo producono.`;

const installazioni = (n) => `${n || 0} ${n === 1 ? "installazione" : "installazioni"}`;

// "Dove migliorare Arturo": la prima cosa del riepilogo del lunedì. Numeri, non verdetti.
export function testoMigliorare(m) {
  if (!m) return [];
  const righe = (elenco, riga, vuoto = "  niente") => elenco && elenco.length ? elenco.map(riga) : [vuoto];
  const per = (a, b) => (b ? `${Math.round((100 * a) / b)}%` : "-");
  const conferma = (x) => `  ${x.valore}  ${x.chiede} / ${x.confermata} / ${per(x.confermata, x.chiede)}, ${installazioni(x.installazioni)}`;
  const r = m.ritenzione || { nuove: 0, soglie: [] };
  return [
    "DOVE MIGLIORARE ARTURO (ultimi 30 giorni, numeri e non verdetti)",
    `Contano solo le installazioni viste dal server in almeno ${LIMITI.giorniGuardie} giorni diversi, salvo la ritenzione.`,
    "",
    `Setup: ${m.setupIniziati || 0} iniziati, ${m.setupFiniti || 0} arrivati in fondo, ${m.setupMai || 0} installazioni nuove che non l'hanno mai lanciato. Fermi da più di 3 giorni, per ultima fase vista:`,
    ...righe(m.setupFermi, (x) => `  ${x.n}  ${x.valore}`, "  nessuno"),
    "",
    `Guardie: contano solo le installazioni viste in almeno ${LIMITI.giorniGuardie} giorni diversi. Una guardia non si allenta sulla sola base di questi numeri.`,
    "Guardie che chiedono conferma (chiede / confermata / quota di sì, installazioni):",
    ...righe(m.confermeGuardie || m.conferme, conferma, "  nessuna"),
    "Per regola, dove la guardia la dice:",
    ...righe((m.conferme || []).filter((x) => x.valore.includes(".py.")), conferma, "  nessuna"),
    "",
    "Guardie che si rompono (volte, installazioni):",
    ...righe(m.errori, (x) => `  ${x.valore}  ${x.n}, ${installazioni(x.installazioni)}`, "  nessuna"),
    "",
    `Rimaste indietro (attive negli ultimi ${LIMITI.fermaGiorni} giorni, senza un rilascio uscito da almeno ${LIMITI.fermaGiorni}):`,
    ...righe(m.indietro, (x) => `  ${corto(x.installazione)}  ferma alla ${x.rilascio}, manca dal ${x.dal}, c'è la ${x.nuovo}`
      + `${x.forma ? `, ${x.forma}` : ""}, ultimo esito ${x.esito || "nessuno"}`, "  nessuna"),
    "",
    "Aggiornamenti non applicati (versione, esito, volte):",
    ...righe(m.aggiornaStorti, (x) => `  ${x.versione}  ${x.valore}  ${x.n}`, "  nessuno"),
    "",
    `Ritenzione: ${r.nuove} installazioni nuove negli ultimi 7 giorni. Per ogni soglia, le installazioni nate nei 30 giorni prima della soglia:`,
    ...r.soglie.map((s) => `  vive dopo ${s.giorni} giorni: ${s.vive} su ${s.idonee} (${per(s.vive, s.idonee)})`),
    "",
    "Versioni di Claude Code (installazioni):",
    ...righe(m.claude, (x) => `  ${x.n}  ${x.valore}`, "  nessun dato"),
    "",
    "---",
    "",
  ];
}

// Per ogni installazione l'elenco corrente della deriva. È un ostacolo se un hook di Arturo è
// spento, se una guardia (hooks/) è modificata, o se un file di Arturo modificato sta insieme a un
// aggiornamento finito in conflitto.
export function testoDeriva(deriva) {
  if (!deriva || !deriva.length) return ["  nessuna"];
  const righe = [];
  for (const d of deriva) {
    // Solo nomi degli elenchi chiusi (finding 37): il testo va anche a /v1/riepilogo, che legge la routine del lunedì.
    const valori = (d.valori || []).map(derivaPubblica);
    const hook = [...new Set(valori.filter((v) => v.startsWith("hook:")).map(derivaInBreve))];
    const file = [...new Set(valori.filter((v) => v.startsWith("file:")).map(derivaInBreve))];
    if (!hook.length && !file.length) { righe.push(`  ${corto(d.installazione)}  rientrata: nessuna differenza che conti`); continue; }
    if (hook.length) righe.push(`  ${corto(d.installazione)}  OSTACOLO, hook di Arturo spenti: ${hook.join(", ")}`);
    const guardie = file.filter((f) => f.startsWith("hooks/"));
    const altri = file.filter((f) => !f.startsWith("hooks/"));
    if (guardie.length) righe.push(`  ${corto(d.installazione)}  OSTACOLO, guardie di Arturo modificate: ${guardie.join(", ")}`);
    if (altri.length) {
      righe.push(`  ${corto(d.installazione)}  ${d.conflitto ? "OSTACOLO, aggiornamento in conflitto, " : ""}file di Arturo modificati: ${altri.join(", ")}`);
    }
  }
  return righe.sort((a, b) => Number(b.includes("OSTACOLO")) - Number(a.includes("OSTACOLO")));
}

// "Chi lo usa" nell'email del lunedì (2/11/2026, #4539): le installazioni attive nella settimana, poi quante
// tacciono. Solo l'id corto: i nomi li conosce la pagina privata dell'admin, non il Worker.
export function testoUso(uso) {
  if (!Array.isArray(uso)) return [];
  const attive = uso.filter((x) => x.giorniAttivi > 0)
    .sort((a, b) => b.giorniAttivi - a.giorniAttivi || b.sessioni - a.sessioni);
  return [
    "Chi lo usa (giorni attivi, sessioni, comando più usato, ultimo giorno):",
    attive.length ? attive.map((x) => `  ${corto(x.installazione)}  ${x.giorniAttivi} giorni, ${x.sessioni} sessioni, ` +
      `${(x.comandi[0] && x.comandi[0].valore) || "nessun comando"}, ultimo ${x.ultima}`).join("\n") : "  nessuna",
    `Installazioni ferme nella settimana: ${uso.length - attive.length}`,
    "",
  ];
}

// I banchi delle guardie rossi (4/11/2026, #4588). Il client manda il nome solo quando l'elenco dei rossi cambia
// (tests/banchi-avvio.sh), con tutti i rossi di quel momento: un banco che resta rosso non si ripete ogni giorno, e il
// testo lo dice.
export function testoBanchi(banchi) {
  const righe = Array.isArray(banchi) ? banchi : [];
  return [
    "Banchi delle guardie rossi sui computer di chi usa Arturo (banco, installazione, versione, primo giorno visto).",
    "Arrivano quando l'elenco dei rossi di un computer cambia: un banco che resta rosso non si ripete ogni giorno.",
    ...(righe.length ? righe.map((x) => `  ${x.valore}  su ${corto(x.installazione)}, ${x.versione}, visto il ${x.dal}`) : ["  nessuno"]),
  ];
}

export function testoRiepilogo(r, titolo, testa = []) {
  const elenco = (righe, vuoto = "nessuno") => righe.length ? righe.map((x) => `  ${x.n}  ${x.valore || "(vuoto)"}`).join("\n") : `  ${vuoto}`;
  const frequenti = r.guardieFrequenti
    ? ["", `Guardie frequenti (almeno ${LIMITI.guardieFrequenti} blocchi nella settimana sulla stessa installazione):`,
      r.guardieFrequenti.length ? r.guardieFrequenti.map((x) => `  ${x.n}  ${x.valore} su ${corto(x.installazione)}`).join("\n") : "  nessuna"]
    : [];
  return [
    titolo,
    "",
    ...testa,
    ...testoMigliorare(r.migliorare),
    `Installazioni attive: ${r.installazioni}`,
    `Sessioni: ${r.sessioni}`,
    "",
    "Config rotte:", elenco(r.config || [], "nessuna"),
    "", ...testoBanchi(r.banchi),
    "", "Deriva dalla config di Arturo:", ...testoDeriva(r.deriva),
    "",
    "Versioni in uso:", elenco(r.versioni, "nessuna"),
    "", "Sistemi:", elenco(r.sistemi),
    "", `Comandi usati (installazioni viste in almeno ${LIMITI.giorniGuardie} giorni):`, elenco(r.comandi),
    "", `Guardie che hanno bloccato (volte, installazioni viste in almeno ${LIMITI.giorniGuardie} giorni):`,
    r.guardie.length ? r.guardie.map((x) => `  ${x.n}  ${x.valore || "(vuoto)"}, ${installazioni(x.installazioni)}`).join("\n") : "  nessuna",
    "", "Esiti di /aggiorna:", elenco(r.aggiorna),
    ...frequenti,
    "", `Segnalazioni ricevute: ${r.segnalazioni}`,
    // I contatori senza id (24/10/2026): eventi fuori elenco scartati, avvisi ed email che non sono partiti.
    "", `Eventi scartati perché fuori elenco: ${r.scartati || 0}`,
    `Avvisi non partiti: Telegram ${r.telegramKo || 0}, email ${r.emailKo || 0}`,
    "",
    ...(testoLancillotto(r.lancillotto) ? [testoLancillotto(r.lancillotto), ""] : []),
    ...testoUso(r.uso),
  ].join("\n");
}

// --- i gestori -----------------------------------------------------------------
// `archivio` e `posta` arrivano da worker.js (D1 e send_email) o da test.mjs (finti).

const giorniFa = (adesso, n) => oggi(new Date(adesso.getTime() - n * 86400000));

// Confronto a tempo costante: il token non si indovina un carattere alla volta.
function stessoToken(dato, atteso) {
  if (typeof dato !== "string" || typeof atteso !== "string" || atteso.length < 32) return false;
  const a = new TextEncoder().encode(dato);
  const b = new TextEncoder().encode(atteso);
  let diverso = a.length ^ b.length;
  for (let i = 0; i < b.length; i++) diverso |= (a[i] ?? 0) ^ b[i];
  return diverso === 0;
}

// Gli avvisi su Telegram a chi mantiene Arturo: un'installazione nuova, una segnalazione. Il testo non porta
// niente più di quello che il server già salva, e mai un id completo: l'installazione esce con 8 caratteri.
export function avvisoInstallazione(riga) {
  return `Arturo: installazione nuova (${riga.installazione.slice(0, 8)}) · ${riga.versione} · ${riga.sistema}`;
}

// Segnalazioni e feedback sono campanelli (24/10/2026): mai titolo né testo. Prima Telegram riceveva il titolo e
// 600 caratteri del testo, e per il feedback l'email della persona e 1500 caratteri: copie fuori dal server, senza
// scadenza, che nessuna cancellazione raggiunge. Il tipo viene da un elenco chiuso. Dal 27/10/2026 la segnalazione
// porta anche da dove arriva (8 caratteri dell'installazione, versione, sistema) e il link alla pagina privata.
export function avvisoSegnalazione(s, numero, leggi = "") {
  const link = linkSegnalazione(leggi, numero);
  return `Arturo: segnalazione n. ${Number(numero)}, ${TIPO_IN_PAROLE[s.tipo] || s.tipo} · ${provenienza(s)}` + (link ? `\n${link}` : "");
}

// Lo sportello (4/11/2026): un seguito o un ritiro, col solo numero.
export function avvisoContributo(numero, cosa) {
  return `Arturo: segnalazione n. ${Number(numero)}, ${cosa === "ritira" ? "ritirata da chi l'ha mandata" : "un seguito di chi l'ha mandata"}`;
}

export function avvisoSetupFinito(riga) {
  return `Arturo: setup finito (${riga.installazione.slice(0, 8)}) · ${riga.versione} · ${riga.sistema}`;
}

export function avvisoIndietro(x) {
  return `Arturo: installazione ${x.installazione.slice(0, 8)} ferma alla ${x.rilascio}, attiva il ${x.ultima}. ` +
    `Non riceve gli aggiornamenti dal ${x.dal}, e c'è la ${x.nuovo}: serve un /aggiorna a mano.`;
}

export function avvisoFeedback(f, numero) {
  return `Arturo: feedback n. ${Number(numero)} · ${f.tipo} · sito`;
}

export function avvisoSito(e, n) {
  const cosa = e.tipo === "download" ? "qualcuno ha copiato il comando di installazione" : "qualcuno ha aperto il repository su GitHub";
  const dove = [e.pagina, e.sistema === "mac" ? "Mac" : e.sistema === "win" ? "Windows" : ""].filter(Boolean).join(", ");
  return `Arturo: ${cosa}${dove ? ` (${dove})` : ""} · ${n}° di oggi`;
}

// Il modulo del sito: testo, tipo, email facoltativa. Il campo "sito" è una trappola invisibile: una persona
// lo lascia vuoto, un bot lo riempie. Il vocale non si accetta più (24/10/2026, decisione 3 del piano della
// telemetria): passava solo a Telegram, che lo teneva senza scadenza e fuori da ogni cancellazione. Un modulo
// con un file nel campo "voce" torna 400 con il motivo, e il file non si legge.
export function validaFeedback(modulo) {
  const campo = (nome) => {
    const v = modulo.get(nome);
    return typeof v === "string" ? v.trim() : "";
  };
  if (campo("sito")) return { trappola: true };
  const testo = campo("testo");
  if (testo.length > LIMITI.feedbackTesto) return { motivo: "testo troppo lungo" };
  const tipo = FEEDBACK_TIPI.includes(campo("tipo")) ? campo("tipo") : "altro";
  const email = campo("email");
  if (email && (email.length > 200 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) return { motivo: "email non valida" };
  const v = modulo.get("voce");
  if (v && typeof v === "object" && v.size > 0) return { motivo: "il vocale non si accetta più: scrivi il messaggio" };
  if (!testo) return { motivo: "scrivi qualcosa" };
  return { feedback: { tipo, testo, email } };
}

// Legge il corpo con un tetto, anche quando manca content-length (invio a pezzi): null se lo supera.
async function corpoLimitato(request, limite) {
  if (!request.body) return new Uint8Array(0);
  const lettore = request.body.getReader();
  const pezzi = [];
  let totale = 0;
  for (;;) {
    const { done, value } = await lettore.read();
    if (done) break;
    totale += value.length;
    if (totale > limite) {
      await lettore.cancel();
      return null;
    }
    pezzi.push(value);
  }
  const tutto = new Uint8Array(totale);
  let i = 0;
  for (const p of pezzi) { tutto.set(p, i); i += p.length; }
  return tutto;
}

export function validaSito(dati) {
  if (!dati || typeof dati !== "object") return { motivo: "corpo mancante" };
  const tipo = SITO_TIPI.includes(dati.tipo) ? dati.tipo : null;
  const pagina = typeof dati.pagina === "string" && /^\/[a-z0-9/-]{0,40}$/.test(dati.pagina) ? dati.pagina : null;
  const sistema = SITO_SISTEMI.includes(dati.sistema || "") ? (dati.sistema || "") : null;
  if (!tipo || pagina === null || sistema === null) return { motivo: "evento del sito non valido" };
  return { evento: { tipo, pagina, sistema } };
}

// Gli avvisi su Telegram: secret TELEGRAM_TOKEN e TELEGRAM_CHAT. Senza, non parte niente. Sta qui e non in worker.js
// (24/10/2026), perché worker.js importa cloudflare:email e node non lo carica: così test.mjs prova che una risposta
// di Telegram che non è ok diventa un errore (V43), che consegna() conta in "telegram-ko". Prima finiva solo nel log
// del Worker, che nessuno legge. `chiama` è fetch, o quello finto del banco.
export function avvisoTelegram(env, chiama = (...a) => fetch(...a)) {
  return async (testo) => {
    if (!env.TELEGRAM_TOKEN || !env.TELEGRAM_CHAT) return;
    const r = await chiama(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT, text: testo, disable_web_page_preview: true }),
    });
    const esito = await r.json().catch(() => ({}));
    if (!esito.ok) throw new Error(`Telegram ha risposto ${r.status}`);
    console.log(`Telegram: messaggio ${esito.result && esito.result.message_id} inviato`);
  };
}

// Un avviso Telegram o un'email che non parte non ferma la richiesta, ma si conta (24/10/2026): prima un canale
// muto non lasciava traccia, e nessuno sapeva che Telegram o la posta tacevano. I contatori "telegram-ko" ed
// "email-ko" non portano id, e compaiono nel recap e nel riepilogo del lunedì. Vero se l'invio è partito.
async function consegna(invio, archivio, giorno, chiave) {
  try {
    await invio();
    return true;
  } catch (e) {
    console.log(chiave === "email-ko" ? "email non partita" : "avviso non partito", e && e.message);
    try {
      await archivio.incrementa(giorno, chiave);
    } catch (e2) {
      console.log("contatore non aggiornato", e2 && e2.message);
    }
    return false;
  }
}

// Le email del cron (recap, riepilogo del lunedì): se la posta fallisce si conta, e il passo risulta fallito.
async function spedisci(archivio, posta, messaggio, adesso) {
  try {
    await posta(messaggio);
  } catch (e) {
    await archivio.incrementa(oggi(adesso), "email-ko").catch(() => {});
    throw e;
  }
}

// `limite(tipo, request)` è il limite per IP del Worker (binding Rate Limiting): falso quando la
// richiesta va oltre. Senza binding, come nei test e in un fork che non lo configura, lascia passare.
export async function gestisci(request, { archivio, posta, avviso = async () => {}, adesso = new Date(), token,
  limite = async () => true, leggi = "" }) {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname === "/") {
    return new Response("Arturo: qui arrivano eventi d'uso, con un id casuale e senza contenuti, segnalazioni e feedback. Codice: https://github.com/stellakamikaze/arturo/tree/main/server\n",
      { headers: { "content-type": "text/plain; charset=utf-8" } });
  }
  // Il riepilogo in JSON, per chi mantiene Arturo: lo legge la routine del lunedì che propone le correzioni.
  if (request.method === "GET" && url.pathname === "/v1/riepilogo") {
    const dato = (request.headers.get("authorization") || "").replace(/^Bearer /, "");
    if (!stessoToken(dato, token)) return risposta(401, { errore: "token mancante o sbagliato" });
    // Senza date, la stessa settimana dell'email del lunedì (26/10/2026, #3892). dal è escluso, come in settimanale.
    const chiesti = { dal: url.searchParams.get("dal") || "", al: url.searchParams.get("al") || "" };
    const settimana = settimanaPrima(adesso);
    let al = GIORNO.test(chiesti.al) ? chiesti.al : null;
    let dal = GIORNO.test(chiesti.dal) ? chiesti.dal : null;
    if (!al && !dal) [dal, al] = [giornoMeno(settimana.lunedi, 1), settimana.domenica];
    al = al || oggi(adesso);
    dal = dal || giorniFa(new Date(`${al}T12:00:00Z`), 7);
    return risposta(200, { dal, al, regola: REGOLA_GUARDIE, ...(await archivio.riepilogo(dal, al, { settimana: true })) });
  }
  // Chi usa Arturo, per la pagina privata dell'admin (2/11/2026, #4539). Stesso token del riepilogo.
  if (request.method === "GET" && url.pathname === "/v1/uso") {
    const dato = (request.headers.get("authorization") || "").replace(/^Bearer /, "");
    if (!stessoToken(dato, token)) return risposta(401, { errore: "token mancante o sbagliato" });
    const chiesto = url.searchParams.get("al") || "";
    const al = GIORNO.test(chiesto) ? chiesto : oggi(adesso);
    const da = url.searchParams.get("dal") || "";
    const dal = GIORNO.test(da) && da < al ? da : giorniFa(new Date(`${al}T12:00:00Z`), 30);
    return risposta(200, { dal, al, installazioni: await archivio.uso(dal, al) });
  }
  // Le segnalazioni, per la pagina privata di chi mantiene Arturo (27/10/2026): l'elenco senza testo, oppure una
  // segnalazione intera. Stesso token del riepilogo: senza, le email restavano l'unica traccia, e il testo si
  // leggeva solo con wrangler.
  const unaSegnalazione = /^\/v1\/segnalazioni\/([0-9]{1,9})$/.exec(url.pathname);
  if (request.method === "GET" && (url.pathname === "/v1/segnalazioni" || unaSegnalazione)) {
    const dato = (request.headers.get("authorization") || "").replace(/^Bearer /, "");
    if (!stessoToken(dato, token)) return risposta(401, { errore: "token mancante o sbagliato" });
    if (!unaSegnalazione) return risposta(200, { segnalazioni: await archivio.segnalazioni(LIMITI.segnalazioniInElenco) });
    const trovata = await archivio.segnalazione(Number(unaSegnalazione[1]));
    return trovata ? risposta(200, trovata) : risposta(404, { errore: "segnalazione inesistente" });
  }
  // Lo sportello (4/11/2026, #3925). Con il token: chi mantiene Arturo scrive stato e risposta. Col codice della
  // ricevuta: la persona legge, aggiunge un seguito, ritira. Codice sbagliato e numero inesistente: stesso 404.
  const contributo = /^\/v1\/contributi\/([0-9]{1,9})(?:\/(seguito|ritira))?$/.exec(url.pathname);
  if (contributo) {
    const numero = Number(contributo[1]);
    const azione = contributo[2] || "";
    const autorizzazione = (request.headers.get("authorization") || "").replace(/^Bearer /, "");
    if (request.method === "POST" && !azione && autorizzazione) {
      if (!stessoToken(autorizzazione, token)) return risposta(401, { errore: "token mancante o sbagliato" });
      const { dati, errore } = await leggiJson(request, LIMITI.risposta * 2);
      if (errore) return errore;
      const { cambi, motivo } = validaRisposta(dati);
      if (motivo) return risposta(400, { errore: motivo });
      const riga = await archivio.aggiornaContributo(numero, cambi, adesso.toISOString());
      return riga ? risposta(200, vistaPersona(riga)) : risposta(404, { errore: "segnalazione inesistente" });
    }
    const nonTrovata = () => risposta(404, { errore: "segnalazione inesistente o codice sbagliato" });
    if (!await limite("moduli", request)) return risposta(429, { errore: "troppe richieste" });
    const codice = (request.headers.get("x-arturo-codice") || "").trim().toLowerCase();
    if (!CODICE.test(codice)) return nonTrovata();
    const riga = await archivio.contributo(numero);
    if (!riga || !riga.codice_hash || !stessoToken(await hashCodice(codice), riga.codice_hash)) return nonTrovata();
    if (request.method === "GET" && !azione) return risposta(200, vistaPersona(riga));
    if (request.method !== "POST" || !azione) return risposta(405, { errore: "metodo non ammesso" });
    const giornoC = oggi(adesso);
    if (azione === "ritira") {
      // Un ritiro ripetuto non suona di nuovo, e l'avviso sta sotto lo stesso tetto del seguito (finding 42): prima
      // un IP mandava un messaggio Telegram ogni sei secondi con un codice preso da una segnalazione mandata da chiunque.
      if ((riga.stato || "") === "ritirata") return risposta(200, { numero, stato: "ritirata" });
      await archivio.ritiraContributo(numero, adesso.toISOString());
      if (await archivio.incrementa(giornoC, "avviso-segnalazione") <= LIMITI.avvisiSegnalazioniPerGiorno) {
        await consegna(() => avviso(avvisoContributo(numero, "ritira")), archivio, giornoC, "telegram-ko");
      }
      return risposta(200, { numero, stato: "ritirata" });
    }
    if ((riga.stato || "") === "ritirata") return risposta(409, { errore: "segnalazione ritirata" });
    const { dati, errore } = await leggiJson(request, LIMITI.seguito * 2);
    if (errore) return errore;
    const testo = testoCorto(dati && dati.testo, LIMITI.seguito);
    if (!testo || !testo.trim()) return risposta(400, { errore: `testo vuoto o oltre ${LIMITI.seguito} caratteri` });
    let seguiti = [];
    try {
      seguiti = JSON.parse(riga.seguiti || "[]") || [];
    } catch {
      seguiti = [];
    }
    if (seguiti.length >= LIMITI.seguitiPerSegnalazione) return risposta(429, { errore: "troppi seguiti per questa segnalazione" });
    seguiti.push({ quando: adesso.toISOString(), testo });
    // Le informazioni chieste sono arrivate: la segnalazione torna da guardare.
    const stato = (riga.stato || "ricevuta") === "serve-info" ? "ricevuta" : (riga.stato || "ricevuta");
    await archivio.seguitoContributo(numero, JSON.stringify(seguiti), stato, adesso.toISOString());
    if (await archivio.incrementa(giornoC, "avviso-segnalazione") <= LIMITI.avvisiSegnalazioniPerGiorno) {
      await consegna(() => avviso(avvisoContributo(numero, "seguito")), archivio, giornoC, "telegram-ko");
    }
    return risposta(201, { numero, seguiti: seguiti.length, stato });
  }
  if (request.method !== "POST") return risposta(405, { errore: "solo POST" });
  const giorno = oggi(adesso);
  // Il modulo e i download arrivano solo dalla landing: un altro sito non li fa inviare ai suoi visitatori.
  const daFuori = (request.headers.get("sec-fetch-site") || "") === "cross-site";
  const telegram = (testo) => consegna(() => avviso(testo), archivio, giorno, "telegram-ko");
  const email = (messaggio) => consegna(() => posta(messaggio), archivio, giorno, "email-ko");

  if (url.pathname === "/v1/eventi") {
    if (!await limite("eventi", request)) return risposta(429, { errore: "troppe richieste" });
    const { dati, errore } = await leggiJson(request, LIMITI.corpoEventi);
    if (errore) return errore;
    const { righe, scartati, installazione, motivo } = validaLotto(dati, giorno);
    if (motivo) return risposta(400, { errore: motivo });
    const gia = await archivio.contaEventi(installazione, giorno);
    if (gia + righe.length > LIMITI.eventiPerGiorno) return risposta(429, { errore: "troppi eventi oggi" });
    const nuova = righe.length > 0 && await archivio.installazioneNuova(installazione);
    // Un id mai visto conta fra le installazioni nuove del giorno (finding 40): oltre il tetto il lotto aspetta domani.
    if (nuova && await archivio.incrementa(giorno, "installazioni-nuove") > LIMITI.installazioniNuovePerGiorno) {
      return risposta(429, { errore: "troppe installazioni nuove oggi" });
    }
    // Una config rotta arriva subito per email, una sola al giorno per installazione. Sta prima del tetto totale
    // (finding 40): un server pieno di eventi finti non spegne l'avviso che dice che le guardie non girano.
    const rotta = righe.find((x) => x.evento === "config");
    if (rotta && await archivio.primaVolta(giorno, `rotta:${rotta.installazione}`)
      && await archivio.incrementa(giorno, "email-rotta") <= LIMITI.emailRottePerGiorno) {
      await email(emailConfigRotta(rotta.installazione, rotta.valore, rotta.versione, { adesso }));
    }
    // Il totale del giorno sta in un contatore: un COUNT(*) su tutti gli eventi a ogni richiesta costa letture di D1.
    if (righe.length && await archivio.incrementa(giorno, "eventi", righe.length) > LIMITI.eventiTotaliPerGiorno) {
      return risposta(429, { errore: "server pieno per oggi" });
    }
    // Gli scartati si contano per giorno, senza l'id: dicono quanti eventi arrivano da client modificati o
    // non allineati. Si contano dopo i tetti, così un lotto rimandato dopo un 429 non conta due volte.
    if (scartati) await archivio.incrementa(giorno, "scartati", scartati);
    if (!righe.length) return risposta(200, { accettati: 0, scartati });
    await archivio.scriviEventi(righe, adesso.toISOString());
    if (nuova && await archivio.incrementa(giorno, "avviso-installazione") <= LIMITI.avvisiInstallazioniPerGiorno) {
      await telegram(avvisoInstallazione(righe[0]));
    }
    // Chi arriva in fondo a /setup, una volta sola per installazione (16/10/2026).
    const finito = righe.find((x) => x.evento === "setup" && x.valore === "fine");
    if (finito && await archivio.primaVolta("sempre", `setup-fine:${finito.installazione}`)
      && await archivio.incrementa(giorno, "avviso-setup") <= LIMITI.avvisiSetupPerGiorno) {
      await telegram(avvisoSetupFinito(finito));
    }
    return risposta(200, { accettati: righe.length, scartati });
  }

  // Lancillotto: stessi tetti per IP e per installazione di Arturo, tabella e avviso suoi.
  if (url.pathname === "/v1/lancillotto/eventi") {
    if (!await limite("eventi", request)) return risposta(429, { errore: "troppe richieste" });
    const { dati, errore } = await leggiJson(request, LIMITI.corpoEventi);
    if (errore) return errore;
    const { righe, scartati, installazione, motivo } = validaLottoLancillotto(dati, giorno,
      { eventiPerLotto: LIMITI.eventiPerLotto, giorniIndietro: LIMITI.giorniIndietro });
    if (motivo) return risposta(400, { errore: motivo });
    const gia = await archivio.contaEventiLancillotto(installazione, giorno);
    if (gia + righe.length > LIMITI.eventiPerGiorno) return risposta(429, { errore: "troppi eventi oggi" });
    if (righe.length && await archivio.incrementa(giorno, "eventi", righe.length) > LIMITI.eventiTotaliPerGiorno) {
      return risposta(429, { errore: "server pieno per oggi" });
    }
    if (scartati) await archivio.incrementa(giorno, "scartati-lancillotto", scartati);
    if (!righe.length) return risposta(200, { accettati: 0, scartati });
    const nuova = await archivio.installazioneNuovaLancillotto(installazione);
    await archivio.scriviEventiLancillotto(righe, adesso.toISOString());
    if (nuova && await archivio.incrementa(giorno, "avviso-installazione") <= LIMITI.avvisiInstallazioniPerGiorno) {
      await telegram(avvisoInstallazioneLancillotto(righe[0]));
    }
    return risposta(200, { accettati: righe.length, scartati });
  }

  if (url.pathname === "/v1/segnalazioni") {
    if (!await limite("moduli", request)) return risposta(429, { errore: "troppe richieste" });
    const { dati, errore } = await leggiJson(request, LIMITI.corpoSegnalazione);
    if (errore) return errore;
    const { segnalazione, motivo, contatto } = validaSegnalazione(dati);
    if (motivo) return risposta(400, { errore: motivo });
    if (await archivio.contaSegnalazioni(giorno) >= LIMITI.segnalazioniPerGiorno) {
      return risposta(429, { errore: "troppe segnalazioni oggi" });
    }
    // La ricevuta (4/11/2026): il codice torna una volta sola, al client. Il server ne tiene l'hash.
    const codice = nuovoCodice();
    const numero = await archivio.salvaSegnalazione({ ...segnalazione, codice_hash: await hashCodice(codice) }, adesso.toISOString());
    if (await archivio.incrementa(giorno, "avviso-segnalazione") <= LIMITI.avvisiSegnalazioniPerGiorno) {
      await telegram(avvisoSegnalazione(segnalazione, numero, leggi));
    }
    let partita = false;
    if (await archivio.incrementa(giorno, "email-segnalazione") <= LIMITI.emailSegnalazioniPerGiorno) {
      partita = await email(emailSegnalazione(segnalazione, numero, { leggi, ricevuta: adesso.toISOString() }));
      if (partita) {
        try {
          await archivio.segnaEmail(numero);
        } catch (e) {
          console.log("email segnata male", e && e.message);
        }
      }
    }
    return risposta(201, { numero, email: partita, codice, ...(contatto ? { contatto } : {}) });
  }

  // Il modulo di feedback del sito, servito dalla landing come /api/feedback. Il testo resta qui, su Telegram
  // va solo il campanello. Il vocale non si accetta più (24/10/2026). Senza JavaScript il modulo arriva come form: la
  // risposta allora è un rimando alla pagina, relativo, perché la richiesta passa dal sito.
  // L'ancora (#inviato, #errore...) fa vedere l'esito con :target, senza script.
  if (url.pathname === "/v1/feedback") {
    const pagina = (request.headers.get("accept") || "").includes("text/html");
    const fine = (status, dati, esito) => (pagina
      ? new Response(null, { status: 303, headers: { location: `/feedback/?${esito}#${esito}` } })
      : risposta(status, dati));
    if (daFuori) return fine(403, { errore: "invio da un altro sito" }, "errore");
    if (!await limite("moduli", request)) return fine(429, { errore: "troppe richieste" }, "troppi");
    if (Number(request.headers.get("content-length") || 0) > LIMITI.feedbackCorpo) {
      return fine(413, { errore: "troppo grande" }, "troppo-grande");
    }
    // Il corpo si legge con il tetto anche senza content-length: un invio a pezzi non riempie la memoria.
    const corpo = await corpoLimitato(request, LIMITI.feedbackCorpo);
    if (corpo === null) return fine(413, { errore: "troppo grande" }, "troppo-grande");
    let modulo;
    try {
      modulo = await new Response(corpo, { headers: { "content-type": request.headers.get("content-type") || "" } }).formData();
    } catch {
      return fine(400, { errore: "modulo non valido" }, "errore");
    }
    const { feedback, motivo, trappola } = validaFeedback(modulo);
    if (trappola) return fine(202, { ricevuto: true }, "inviato");
    if (motivo) return fine(400, { errore: motivo }, "errore");
    if (await archivio.incrementa(giorno, "feedback") > LIMITI.feedbackPerGiorno) {
      return fine(429, { errore: "troppi messaggi oggi" }, "troppi");
    }
    const numero = await archivio.salvaFeedback(feedback, adesso.toISOString());
    await telegram(avvisoFeedback(feedback, numero));
    return fine(201, { numero }, "inviato");
  }

  // I download dal sito: il comando di installazione copiato, o il repository aperto.
  if (url.pathname === "/v1/sito") {
    if (daFuori) return risposta(403, { errore: "invio da un altro sito" });
    if (!await limite("moduli", request)) return risposta(429, { errore: "troppe richieste" });
    const { dati, errore } = await leggiJson(request, 2048);
    if (errore) return errore;
    const { evento, motivo } = validaSito(dati);
    if (motivo) return risposta(400, { errore: motivo });
    const n = await archivio.incrementa(giorno, `sito:${evento.tipo}`);
    if (n <= LIMITI.sitoPerGiorno) await telegram(avvisoSito(evento, n));
    return risposta(202, { ricevuto: true });
  }

  return risposta(404, { errore: "percorso sconosciuto" });
}

// Il recap del giorno prima. Nei giorni senza eventi né segnalazioni non parte (14/10/2026,
// Federico): un'email di zeri ogni mattina insegna a non leggerla. Il segno di vita del server
// è il riepilogo del lunedì, che parte sempre: se manca quello, il Worker è fermo.
export async function giornaliero({ archivio, posta, adesso = new Date(), leggi = "" }) {
  const ieri = giorniFa(adesso, 1);
  const r = await archivio.riepilogo(giorniFa(adesso, 2), ieri);
  // Dal 5/11/2026 il recap dice anche chi ha usato Arturo e come (archivio.giorno). Un archivio senza giorno() resta
  // al riepilogo di prima.
  const g = archivio.giorno ? await archivio.giorno(ieri) : null;
  // Anche un giorno con soli eventi scartati o canali muti merita il recap: non è un giorno di zeri (24/10/2026).
  // Un feedback o un download dal sito, dal 5/11/2026, anche.
  if (!r.installazioni && !r.segnalazioni && !r.scartati && !r.telegramKo && !r.emailKo
    && !(g && (g.feedback || g.download || g.github))) return;
  const { html, task: daFare } = recapGiorno(r, g, { giorno: ieri, leggi });
  await spedisci(archivio, posta, { oggetto: `[Arturo] Recap del ${ieri}`,
    testo: testoRiepilogo(r, `Arturo, il giorno ${ieri}`, righeGiorno(r, g, { giorno: ieri })), html, task: daFare }, adesso);
}

// Il giorno di calendario in Europe/Rome: il cron del Worker gira in UTC (wrangler.toml), le settimane di
// Federico no. "2026-10-26" alle 06:00 UTC del 26/10, e anche alle 23:30 UTC del 25/10.
export function giornoRoma(adesso = new Date()) {
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Rome", year: "numeric", month: "2-digit",
    day: "2-digit" }).formatToParts(adesso).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}`;
}

const giornoDellaSettimana = (giorno) => new Date(`${giorno}T12:00:00Z`).getUTCDay();

// La settimana del riepilogo: da lunedì a domenica, l'ultima finita prima di oggi in ora di Roma (24/10/2026).
// Prima andava da oggi meno 7 escluso a oggi incluso: il lunedì di sette giorni prima restava fuori,
// entrava il lunedì appena cominciato, e il titolo mostrava otto date.
export function settimanaPrima(adesso = new Date()) {
  const oggiRoma = giornoRoma(adesso);
  const domenica = giornoMeno(oggiRoma, giornoDellaSettimana(oggiRoma) || 7);
  return { lunedi: giornoMeno(domenica, 6), domenica };
}

export async function settimanale({ archivio, posta, adesso = new Date() }) {
  const { lunedi, domenica } = settimanaPrima(adesso);
  // archivio.riepilogo esclude il primo giorno (giorno > dal): si parte dalla domenica prima del lunedì.
  const r = await archivio.riepilogo(giornoMeno(lunedi, 1), domenica, { settimana: true });
  const { html, task: daFare } = recapSettimana(r, { lunedi, domenica });
  await spedisci(archivio, posta, { oggetto: `[Arturo] Riepilogo della settimana ${lunedi} - ${domenica}`,
    testo: testoRiepilogo(r, `Arturo, settimana dal ${lunedi} al ${domenica}`), html, task: daFare }, adesso);
}

// La pulizia del lunedì: eventi, contatori, feedback e segnalazioni più vecchi di 12 mesi. Il pacchetto tecnico
// delle segnalazioni si svuota dopo 90 giorni (4/11/2026).
export async function pulizia({ archivio, adesso = new Date() }) {
  await archivio.pulisci(giorniFa(adesso, LIMITI.conservazioneGiorni));
  await archivio.svuotaPacchetti(giorniFa(adesso, LIMITI.pacchettoGiorni));
}

// Le installazioni rimaste indietro, su Telegram ogni mattina: una volta ogni avvisoIndietroOgni giorni per
// installazione, perché il guasto non si ripara da solo e va sbloccato a mano (23/10/2026).
export async function avvisiIndietro({ archivio, avviso, adesso = new Date() }) {
  const al = oggi(adesso);
  let mandati = 0;
  for (const x of await archivio.indietro(al)) {
    if (mandati >= LIMITI.avvisiIndietroPerGiorno) break;
    const chiave = `indietro:${x.installazione}`;
    const ultimo = await archivio.ultimoAvviso(chiave);
    if (ultimo && ultimo > giornoMeno(al, LIMITI.avvisoIndietroOgni)) continue;
    await archivio.incrementa(al, chiave);
    await consegna(() => avviso(avvisoIndietro(x)), archivio, al, "telegram-ko");
    mandati++;
  }
}

// Il cron gira ogni mattina alle 6 UTC: il recap del giorno prima se c'è qualcosa, le installazioni rimaste
// indietro, il lunedì (in ora di Roma) sempre la settimana e poi la pulizia. Ogni passo ha il suo try (24/10/2026):
// prima un'email del recap fallita fermava gli avvisi e il riepilogo del lunedì, che è il segno di vita del Worker.
// L'errore va nel log del Worker con il nome del passo. Finiti tutti i passi, se uno è fallito, programmato
// rilancia un errore unico con i nomi in .falliti: così il cron risulta fallito anche negli eventi di Cloudflare.
export async function programmato({ archivio, posta, avviso = async () => {}, adesso = new Date(), leggi = "" }) {
  const passi = [
    ["recap", () => giornaliero({ archivio, posta, adesso, leggi })],
    ["indietro", () => avvisiIndietro({ archivio, avviso, adesso })],
  ];
  if (giornoDellaSettimana(giornoRoma(adesso)) === 1) {
    passi.push(["settimana", () => settimanale({ archivio, posta, adesso })], ["pulizia", () => pulizia({ archivio, adesso })]);
  }
  const falliti = [];
  for (const [nome, passo] of passi) {
    try {
      await passo();
    } catch (e) {
      falliti.push(nome);
      console.error(`cron: il passo ${nome} non è riuscito:`, e && e.message);
    }
  }
  if (falliti.length) throw Object.assign(new Error(`cron: passi non riusciti: ${falliti.join(", ")}`), { falliti });
}
